import hashlib
import hmac
import logging
from decimal import Decimal

from django.conf import settings
from django.db import transaction

from customer.models import Customer, CustomerAddress
from product.models import Product, ProductVariant
from user.models import User
from .models import Order, OrderItem, Payment

logger = logging.getLogger(__name__)


class InsufficientStockError(Exception):
    """Se lanza cuando no hay stock suficiente para un producto."""
    pass


def get_or_create_customer(data):
    """
    Busca un Customer por email.
    Si no existe, crea User (sin contraseña) + Customer.
    Retorna el Customer.
    """
    email = data['email'].lower().strip()

    try:
        customer = Customer.objects.get(email=email)
        # Actualizar datos si vienen nuevos
        customer.first_name = data.get('first_name', customer.first_name)
        customer.last_name = data.get('last_name', customer.last_name)
        customer.phone = data.get('phone', customer.phone)
        customer.document_number = data.get('document_number', customer.document_number)
        customer.save()
        return customer
    except Customer.DoesNotExist:
        pass

    # Crear User sin contraseña
    user = User.objects.filter(email=email).first()
    if not user:
        user = User(
            username=email,
            email=email,
            first_name=data.get('first_name', ''),
            last_name=data.get('last_name', ''),
        )
        user.set_unusable_password()
        user.save()

    customer = Customer.objects.create(
        user=user,
        first_name=data.get('first_name', ''),
        last_name=data.get('last_name', ''),
        email=email,
        phone=data.get('phone'),
        document_number=data.get('document_number', ''),
    )

    # Guardar dirección
    if data.get('address'):
        CustomerAddress.objects.create(
            customer=customer,
            address=data.get('address', ''),
            city=data.get('city', ''),
            state=data.get('state', ''),
            country=data.get('country', 'Colombia'),
            postal_code=data.get('postal_code', ''),
        )

    return customer


@transaction.atomic
def create_order(data, items):
    """
    Crea una orden completa:
    1. Obtiene/crea Customer
    2. Valida y reserva stock (select_for_update)
    3. Crea Order + OrderItems
    4. Crea Payment pendiente
    Retorna la Order creada.
    """
    customer = get_or_create_customer(data)

    # Calcular subtotal y validar stock
    subtotal = Decimal('0')
    validated_items = []

    for item in items:
        product_id = item['id']
        variant_id = item.get('variantId') or 0
        qty = int(item['qty'])
        price = Decimal(str(item['price']))

        if variant_id:
            variant = (
                ProductVariant.objects
                .select_for_update()
                .get(id=variant_id, product_id=product_id)
            )
            if variant.stock < qty:
                raise InsufficientStockError(
                    f'Stock insuficiente para "{variant.product.name} – {variant.sku}". '
                    f'Disponible: {variant.stock}, solicitado: {qty}'
                )
            variant.stock -= qty
            variant.save(update_fields=['stock'])
            product = variant.product
        else:
            product = (
                Product.objects
                .select_for_update()
                .get(id=product_id)
            )
            current_stock = product.stock or 0
            if current_stock < qty:
                raise InsufficientStockError(
                    f'Stock insuficiente para "{product.name}". '
                    f'Disponible: {current_stock}, solicitado: {qty}'
                )
            product.stock = current_stock - qty
            product.save(update_fields=['stock'])
            variant = None

        line_total = price * qty
        subtotal += line_total

        validated_items.append({
            'product': product,
            'variant': variant,
            'product_name': item.get('name', product.name),
            'product_image': item.get('image', ''),
            'sku': item.get('sku', ''),
            'attributes': item.get('attributes', {}),
            'price': price,
            'quantity': qty,
            'total': line_total,
        })

    shipping_cost = Decimal(str(data.get('shipping_cost', 0)))
    total = subtotal + shipping_cost

    order = Order.objects.create(
        customer=customer,
        email=data['email'],
        first_name=data['first_name'],
        last_name=data['last_name'],
        phone=data['phone'],
        document_number=data.get('document_number', ''),
        address=data['address'],
        address2=data.get('address2', ''),
        city=data['city'],
        state=data.get('state', ''),
        country=data.get('country', 'Colombia'),
        postal_code=data.get('postal_code', ''),
        notes=data.get('notes', ''),
        payment_method=data['payment_method'],
        subtotal=subtotal,
        shipping_cost=shipping_cost,
        total=total,
    )

    for vi in validated_items:
        OrderItem.objects.create(
            order=order,
            product=vi['product'],
            variant=vi['variant'],
            product_name=vi['product_name'],
            product_image=vi['product_image'],
            sku=vi['sku'],
            attributes=vi['attributes'],
            price=vi['price'],
            quantity=vi['quantity'],
            total=vi['total'],
        )

    Payment.objects.create(
        order=order,
        provider=data['payment_method'],
        amount=total,
        status=Payment.Status.PENDING,
    )

    return order


@transaction.atomic
def restore_stock(order):
    """Restaura el stock cuando un pago es rechazado o cancelado."""
    for item in order.items.select_related('product', 'variant'):
        if item.variant:
            variant = (
                ProductVariant.objects
                .select_for_update()
                .get(id=item.variant_id)
            )
            variant.stock += item.quantity
            variant.save(update_fields=['stock'])
        elif item.product:
            product = (
                Product.objects
                .select_for_update()
                .get(id=item.product_id)
            )
            product.stock = (product.stock or 0) + item.quantity
            product.save(update_fields=['stock'])


# ── Mercado Pago ─────────────────────────────────────────────
def create_mercadopago_preference(order):
    """
    Crea una Preference en Mercado Pago y retorna la URL de pago.
    """
    import mercadopago
    sdk = mercadopago.SDK(settings.MERCADOPAGO_ACCESS_TOKEN)

    items = []
    for item in order.items.all():
        items.append({
            "title": item.product_name,
            "quantity": item.quantity,
            "unit_price": float(item.price),
            "currency_id": "COP",
            "picture_url": item.product_image or "",
        })

    if order.shipping_cost > 0:
        items.append({
            "title": "Envío estándar",
            "quantity": 1,
            "unit_price": float(order.shipping_cost),
            "currency_id": "COP",
        })

    base_url = settings.SITE_URL
    preference_data = {
        "items": items,
        "payer": {
            "name": order.first_name,
            "surname": order.last_name,
            "email": order.email,
            "phone": {"number": order.phone},
        },
        "back_urls": {
            "success": f"{base_url}/checkout/resultado/?order={order.order_number}",
            "failure": f"{base_url}/checkout/resultado/?order={order.order_number}",
            "pending": f"{base_url}/checkout/resultado/?order={order.order_number}",
        },
        "auto_return": "approved",
        "external_reference": order.order_number,
        "notification_url": f"{base_url}/api/order/webhooks/mercadopago/",
    }

    result = sdk.preference().create(preference_data)
    logger.info("MercadoPago raw result: status=%s response=%s", result.get("status"), result.get("response"))

    if result.get("status") not in (200, 201):
        raise Exception(f"MercadoPago API error: status={result.get('status')} response={result.get('response')}")

    preference = result["response"]

    return {
        "id": preference["id"],
        "init_point": preference["init_point"],
        "sandbox_init_point": preference.get("sandbox_init_point", ""),
    }


def handle_mercadopago_webhook(payload):
    """
    Procesa notificaciones de Mercado Pago.
    Soporta todos los tipos de evento: payment, merchant_order,
    chargebacks, delivery, point_integration_wh, etc.
    Retorna dict con resultado del procesamiento.
    """
    import mercadopago
    from .models import WebhookLog

    event_type = payload.get('type') or payload.get('topic', 'unknown')
    event_id = str(payload.get('id', ''))
    resource_id = str(payload.get('data', {}).get('id', ''))
    action = payload.get('action', '')

    sdk = mercadopago.SDK(settings.MERCADOPAGO_ACCESS_TOKEN)
    result_info = {'event_type': event_type, 'action': action}

    # ── payment ──────────────────────────────────────────────
    if event_type == 'payment':
        return _handle_mp_payment(sdk, resource_id, payload)

    # ── merchant_order ───────────────────────────────────────
    if event_type == 'merchant_order' or payload.get('topic') == 'merchant_orders':
        return _handle_mp_merchant_order(sdk, resource_id or event_id, payload)

    # ── chargebacks (contracargos) ───────────────────────────
    if event_type == 'chargebacks':
        return _handle_mp_chargeback(sdk, resource_id, payload)

    # ── delivery (envíos MP) ─────────────────────────────────
    if event_type in ('delivery', 'shipments'):
        return _handle_mp_delivery(resource_id, payload)

    # ── point_integration_wh (Point) ─────────────────────────
    if event_type == 'point_integration_wh':
        return _handle_mp_point(resource_id, payload)

    # ── subscription / plans ─────────────────────────────────
    if event_type in ('subscription_preapproval', 'subscription_preapproval_plan',
                       'subscription_authorized_payment'):
        return _handle_mp_subscription(event_type, resource_id, payload)

    # ── Eventos no manejados: loguear y guardar ──────────────
    logger.info("MP webhook tipo no manejado: type=%s action=%s", event_type, action)
    WebhookLog.objects.create(
        provider='mercadopago',
        event_type=event_type,
        event_id=event_id,
        resource_id=resource_id,
        payload=payload,
        processed=False,
        error_message=f'Tipo de evento no manejado: {event_type}',
    )
    return {'status': 'ignored', 'event_type': event_type}


def _handle_mp_payment(sdk, payment_id, payload):
    """Procesa notificaciones de tipo payment."""
    from .models import WebhookLog

    if not payment_id:
        logger.warning("MP payment webhook sin payment_id: %s", payload)
        return {'status': 'error', 'detail': 'missing payment_id'}

    # Consultar el pago a la API de MP
    result = sdk.payment().get(payment_id)
    api_status = result.get("status")
    mp_payment = result.get("response", {})

    logger.info("MP payment lookup: api_status=%s mp_status=%s payment_id=%s",
                api_status, mp_payment.get("status"), payment_id)

    if api_status != 200:
        logger.error("MP payment lookup failed: %s", result)
        WebhookLog.objects.create(
            provider='mercadopago', event_type='payment',
            resource_id=str(payment_id), payload=payload,
            response_data=mp_payment, processed=False,
            error_message=f'API lookup failed: status={api_status}',
        )
        return {'status': 'error', 'detail': f'api_status={api_status}'}

    order_number = mp_payment.get("external_reference")
    if not order_number:
        logger.warning("MP payment sin external_reference: payment_id=%s", payment_id)
        WebhookLog.objects.create(
            provider='mercadopago', event_type='payment',
            resource_id=str(payment_id), payload=payload,
            response_data=mp_payment, processed=False,
            error_message='Sin external_reference',
        )
        return {'status': 'error', 'detail': 'no external_reference'}

    try:
        order = Order.objects.get(order_number=order_number)
    except Order.DoesNotExist:
        logger.error("Orden no encontrada para webhook: %s", order_number)
        WebhookLog.objects.create(
            provider='mercadopago', event_type='payment',
            resource_id=str(payment_id), payload=payload,
            response_data=mp_payment, processed=False,
            error_message=f'Orden no encontrada: {order_number}',
        )
        return {'status': 'error', 'detail': f'order not found: {order_number}'}

    mp_status = mp_payment.get("status")

    # Mapear estados de MP a nuestros estados
    status_map = {
        'approved':   (Payment.Status.APPROVED, Order.Status.APPROVED),
        'authorized': (Payment.Status.APPROVED, Order.Status.APPROVED),
        'rejected':   (Payment.Status.REJECTED, Order.Status.REJECTED),
        'cancelled':  (Payment.Status.REJECTED, Order.Status.CANCELLED),
        'refunded':   (Payment.Status.REFUNDED, Order.Status.CANCELLED),
        'charged_back': (Payment.Status.REJECTED, Order.Status.CANCELLED),
        'in_process': (Payment.Status.PENDING, Order.Status.PENDING_PAYMENT),
        'in_mediation': (Payment.Status.PENDING, Order.Status.PENDING_PAYMENT),
        'pending':    (Payment.Status.PENDING, Order.Status.PENDING_PAYMENT),
    }

    payment_status, order_status = status_map.get(
        mp_status,
        (Payment.Status.PENDING, Order.Status.PENDING_PAYMENT)
    )

    # Actualizar Payment
    payment = order.payments.first()
    if payment:
        payment.transaction_id = str(payment_id)
        payment.status = payment_status
        payment.raw_response = mp_payment
        payment.save()

    # Actualizar Order y stock
    old_status = order.status
    order.status = order_status
    order.save(update_fields=['status', 'updated_at'])

    # Si pasa a rechazado/cancelado y antes estaba pendiente, restaurar stock
    if order_status in (Order.Status.REJECTED, Order.Status.CANCELLED):
        if old_status == Order.Status.PENDING_PAYMENT:
            restore_stock(order)

    # Guardar log
    WebhookLog.objects.create(
        provider='mercadopago', event_type='payment',
        resource_id=str(payment_id), order=order,
        payload=payload, response_data=mp_payment,
        processed=True,
    )

    logger.info(
        "MP payment processed: order=%s mp_status=%s -> order_status=%s",
        order_number, mp_status, order_status
    )
    return {'status': 'processed', 'order': order_number, 'mp_status': mp_status}


def _handle_mp_merchant_order(sdk, order_id, payload):
    """Procesa notificaciones de merchant_order (orden comercial)."""
    from .models import WebhookLog

    result = sdk.merchant_order().get(order_id)
    api_status = result.get("status")
    mp_order = result.get("response", {})

    logger.info("MP merchant_order: api_status=%s order_id=%s", api_status, order_id)

    external_ref = mp_order.get("external_reference", "")
    order = None
    if external_ref:
        order = Order.objects.filter(order_number=external_ref).first()

    # Verificar si todos los pagos de la orden están aprobados
    payments = mp_order.get("payments", [])
    total_paid = sum(
        p.get("transaction_amount", 0) for p in payments
        if p.get("status") == "approved"
    )
    total_order = mp_order.get("total_amount", 0)

    processed = False
    if order and total_paid >= total_order and total_order > 0:
        if order.status == Order.Status.PENDING_PAYMENT:
            order.status = Order.Status.APPROVED
            order.save(update_fields=['status', 'updated_at'])
            payment_obj = order.payments.first()
            if payment_obj:
                payment_obj.status = Payment.Status.APPROVED
                payment_obj.save(update_fields=['status'])
            processed = True
            logger.info("MP merchant_order approved: order=%s total_paid=%s",
                        external_ref, total_paid)

    WebhookLog.objects.create(
        provider='mercadopago', event_type='merchant_order',
        resource_id=str(order_id), order=order,
        payload=payload, response_data=mp_order,
        processed=processed,
    )
    return {'status': 'processed' if processed else 'logged', 'order_id': order_id}


def _handle_mp_chargeback(sdk, chargeback_id, payload):
    """Procesa notificaciones de contracargos (chargebacks)."""
    from .models import WebhookLog

    logger.warning("MP chargeback recibido: id=%s payload=%s", chargeback_id, payload)

    # Intentar obtener el pago asociado desde el payload
    payment_id = payload.get('data', {}).get('id', chargeback_id)
    order = None

    if payment_id:
        result = sdk.payment().get(payment_id)
        mp_payment = result.get("response", {})
        external_ref = mp_payment.get("external_reference", "")
        if external_ref:
            order = Order.objects.filter(order_number=external_ref).first()
            if order and order.status != Order.Status.CANCELLED:
                old_status = order.status
                order.status = Order.Status.CANCELLED
                order.save(update_fields=['status', 'updated_at'])
                payment_obj = order.payments.first()
                if payment_obj:
                    payment_obj.status = Payment.Status.REJECTED
                    payment_obj.raw_response = {**payment_obj.raw_response, 'chargeback': payload}
                    payment_obj.save()
                if old_status == Order.Status.PENDING_PAYMENT:
                    restore_stock(order)
                logger.warning("MP chargeback: orden %s cancelada", external_ref)

    WebhookLog.objects.create(
        provider='mercadopago', event_type='chargebacks',
        resource_id=str(chargeback_id), order=order,
        payload=payload, processed=order is not None,
    )
    return {'status': 'processed', 'chargeback_id': chargeback_id}


def _handle_mp_delivery(resource_id, payload):
    """Procesa notificaciones de envíos de Mercado Pago."""
    from .models import WebhookLog

    logger.info("MP delivery webhook: resource_id=%s", resource_id)

    WebhookLog.objects.create(
        provider='mercadopago', event_type='delivery',
        resource_id=str(resource_id),
        payload=payload, processed=True,
    )
    return {'status': 'logged', 'resource_id': resource_id}


def _handle_mp_point(resource_id, payload):
    """Procesa notificaciones de Point (integraciones presenciales)."""
    from .models import WebhookLog

    logger.info("MP Point webhook: resource_id=%s", resource_id)

    WebhookLog.objects.create(
        provider='mercadopago', event_type='point_integration_wh',
        resource_id=str(resource_id),
        payload=payload, processed=True,
    )
    return {'status': 'logged', 'resource_id': resource_id}


def _handle_mp_subscription(event_type, resource_id, payload):
    """Procesa notificaciones de suscripciones y planes."""
    from .models import WebhookLog

    logger.info("MP subscription webhook: type=%s resource_id=%s", event_type, resource_id)

    WebhookLog.objects.create(
        provider='mercadopago', event_type=event_type,
        resource_id=str(resource_id),
        payload=payload, processed=True,
    )
    return {'status': 'logged', 'event_type': event_type}
