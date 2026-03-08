import json
import logging

from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status

from order.models import Order
from order.services import (
    create_order,
    InsufficientStockError,
    create_mercadopago_preference,
    handle_mercadopago_webhook,
)
from metodos_pagos.models import PaymentMethod
from .serializers import OrderDetailSerializer, OrderListSerializer

logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([AllowAny])
def create_order_view(request):
    """
    Crea una orden desde el checkout.
    Body esperado:
    {
        "customer": { first_name, last_name, email, phone, document_number,
                      address, address2, city, state, country, postal_code, notes },
        "items": [ { id, variantId, name, price, qty, image, sku, attributes } ],
        "payment_method": "mercadopago" | "wompi" | "paypal",
        "shipping_cost": 10000
    }
    """
    data = request.data
    customer_data = data.get('customer', {})
    items = data.get('items', [])
    payment_method = data.get('payment_method', '')
    shipping_cost = data.get('shipping_cost', 0)

    # Validaciones básicas
    required = ['first_name', 'last_name', 'email', 'phone', 'address', 'city']
    missing = [f for f in required if not customer_data.get(f)]
    if missing:
        return Response(
            {'error': f'Campos obligatorios faltantes: {", ".join(missing)}'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if not items:
        return Response(
            {'error': 'El carrito está vacío.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if not payment_method:
        return Response(
            {'error': 'Selecciona un método de pago.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    customer_data['payment_method'] = payment_method
    customer_data['shipping_cost'] = shipping_cost

    try:
        order = create_order(customer_data, items)
    except InsufficientStockError as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_409_CONFLICT,
        )
    except Exception as e:
        logger.exception("Error creando orden")
        return Response(
            {'error': 'Error interno al procesar tu pedido. Intenta nuevamente.'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    response_data = {
        'order_number': order.order_number,
        'total': float(order.total),
    }

    # Buscar metodo de pago activo en la DB
    pm = PaymentMethod.objects.filter(
        provider=payment_method, is_active=True, deleted_at__isnull=True
    ).first()

    if not pm:
        logger.warning("Metodo de pago no encontrado o inactivo: %s", payment_method)
        response_data['error_payment'] = f'El metodo de pago "{payment_method}" no esta disponible.'
        return Response(response_data, status=status.HTTP_201_CREATED)

    # Crear preference según pasarela
    if payment_method == 'mercadopago':
        try:
            mp_result = create_mercadopago_preference(order, access_token=pm.access_token)
            response_data['redirect_url'] = mp_result['init_point']
            response_data['preference_id'] = mp_result['id']
            response_data['sandbox_init_point'] = mp_result['sandbox_init_point']
        except Exception as e:
            logger.exception("Error creando preference de MercadoPago")
            response_data['redirect_url'] = None
            response_data['error_payment'] = 'No se pudo conectar con MercadoPago. Tu orden fue creada, intenta pagar desde tu perfil.'

    # TODO: Implementar wompi y paypal cuando estén listos
    # elif payment_method == 'wompi': ...
    # elif payment_method == 'paypal': ...

    return Response(response_data, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([AllowAny])
def order_detail_view(request, order_number):
    """Detalle de una orden por su número."""
    try:
        order = Order.objects.prefetch_related('items', 'payments').get(
            order_number=order_number
        )
    except Order.DoesNotExist:
        return Response(
            {'error': 'Orden no encontrada.'},
            status=status.HTTP_404_NOT_FOUND,
        )
    serializer = OrderDetailSerializer(order)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def order_list_view(request):
    """Lista de órdenes (para admin o panel)."""
    orders = Order.objects.prefetch_related('items').all()

    # Filtros opcionales
    search = request.query_params.get('search', '')
    if search:
        from django.db.models import Q
        orders = orders.filter(
            Q(order_number__icontains=search) |
            Q(email__icontains=search) |
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search)
        )

    status_filter = request.query_params.get('status', '')
    if status_filter:
        orders = orders.filter(status=status_filter)

    serializer = OrderListSerializer(orders, many=True)
    return Response(serializer.data)


@csrf_exempt
def webhook_mercadopago(request):
    """
    Webhook que recibe notificaciones de Mercado Pago.
    POST /api/order/webhooks/mercadopago/

    Soporta eventos: payment, merchant_order, chargebacks, delivery,
    point_integration_wh, subscription_preapproval, etc.

    MercadoPago envía query params: ?id=xxx&topic=yyy (formato viejo)
    o body JSON con {type, data.id, action} (formato nuevo v2).
    """
    if request.method == 'GET':
        # MP a veces envía un GET de verificación
        return JsonResponse({'status': 'ok'})

    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    # Parsear body
    try:
        if request.body:
            payload = json.loads(request.body)
        else:
            payload = {}
    except json.JSONDecodeError:
        logger.warning("MP webhook: JSON inválido recibido")
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    # Soportar formato viejo por query params (?id=xxx&topic=payment)
    query_id = request.GET.get('id')
    query_topic = request.GET.get('topic')
    if query_topic and not payload.get('type'):
        payload['type'] = query_topic
    if query_id and not payload.get('data', {}).get('id'):
        payload.setdefault('data', {})['id'] = query_id

    event_type = payload.get('type') or payload.get('topic', 'unknown')

    logger.info(
        "MP webhook received: type=%s action=%s data_id=%s query_id=%s query_topic=%s",
        event_type,
        payload.get('action', ''),
        payload.get('data', {}).get('id', ''),
        query_id,
        query_topic,
    )

    try:
        result = handle_mercadopago_webhook(payload)
        logger.info("MP webhook result: %s", result)
    except Exception as e:
        logger.exception("Error processing MP webhook: type=%s", event_type)
        from order.models import WebhookLog
        WebhookLog.objects.create(
            provider='mercadopago',
            event_type=event_type,
            resource_id=str(payload.get('data', {}).get('id', '')),
            payload=payload,
            processed=False,
            error_message=str(e),
        )

    # Siempre responder 200 para que MP no reintente
    return JsonResponse({'status': 'ok'})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def sales_report_view(request):
    """Reporte de ventas y productos vendidos."""
    from django.db.models import Sum, Count, F

    approved_orders = Order.objects.filter(status__in=[
        Order.Status.APPROVED,
        Order.Status.SHIPPED,
        Order.Status.DELIVERED,
    ])

    # Totales generales
    totals = approved_orders.aggregate(
        total_orders=Count('id'),
        total_revenue=Sum('total'),
    )

    # Órdenes por estado
    orders_by_status = dict(
        Order.objects.values_list('status')
        .annotate(count=Count('id'))
        .values_list('status', 'count')
    )

    # Top productos vendidos
    from order.models import OrderItem
    top_products = (
        OrderItem.objects
        .filter(order__status__in=[
            Order.Status.APPROVED,
            Order.Status.SHIPPED,
            Order.Status.DELIVERED,
        ])
        .values('product_name')
        .annotate(
            units_sold=Sum('quantity'),
            revenue=Sum('total'),
        )
        .order_by('-units_sold')[:10]
    )

    return Response({
        'total_orders': totals['total_orders'] or 0,
        'total_revenue': float(totals['total_revenue'] or 0),
        'orders_by_status': orders_by_status,
        'top_products': list(top_products),
    })
