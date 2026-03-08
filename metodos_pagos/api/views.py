from rest_framework.decorators  import api_view, permission_classes
from django.shortcuts           import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination  import PageNumberPagination
from rest_framework.response    import Response
from rest_framework             import status
from django.core.files.storage  import default_storage
from django.utils               import timezone
from django.db.models           import Q
from metodos_pagos.models       import PaymentMethod
from .serializers               import (
    PaymentMethodSerializer, PaymentMethodListSerializer,
    PaymentMethodDetailSerializer, PaymentMethodUpdateSerializer,
)


def _delete_s3_image(image_field):
    """Elimina el archivo de S3 asociado a un FileField. Silencia errores."""
    if image_field:
        try:
            default_storage.delete(image_field.name)
        except Exception:
            pass


# ── POST /api/metodos-pagos/create/ ────────────────────────────────────────
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_data(request):
    serializer = PaymentMethodSerializer(data=request.data)
    if serializer.is_valid():
        payment_method = serializer.save(user=request.user)
        return Response(
            {'message': 'Payment method created successfully.', 'data': PaymentMethodDetailSerializer(payment_method).data},
            status=status.HTTP_201_CREATED
        )
    return Response({'message': 'Invalid data.', 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


# ── GET /api/metodos-pagos/all/ ────────────────────────────────────────────
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_all_data(request):
    deleted_param = request.GET.get('deleted', 'false')
    if deleted_param.lower() == 'true':
        methods = PaymentMethod.objects.filter(deleted_at__isnull=False)
    else:
        methods = PaymentMethod.objects.filter(deleted_at__isnull=True)

    search = request.GET.get('search', None)
    if search:
        methods = methods.filter(
            Q(name__icontains=search) |
            Q(provider__icontains=search) |
            Q(description__icontains=search)
        )

    environment = request.GET.get('environment', None)
    if environment:
        methods = methods.filter(environment=environment)

    is_active = request.GET.get('is_active', None)
    if is_active is not None:
        methods = methods.filter(is_active=is_active.lower() == 'true')

    paginator = PageNumberPagination()
    paginator.page_size             = 10
    paginator.page_size_query_param = 'page_size'
    paginator.max_page_size         = 100

    result_page = paginator.paginate_queryset(methods, request)
    serializer  = PaymentMethodListSerializer(result_page, many=True)
    return paginator.get_paginated_response(serializer.data)


# ── GET /api/metodos-pagos/<id>/ ───────────────────────────────────────────
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_by_id(request, id):
    payment_method = get_object_or_404(PaymentMethod, id=id)
    serializer     = PaymentMethodDetailSerializer(payment_method)
    return Response(serializer.data, status=status.HTTP_200_OK)


# ── PUT /api/metodos-pagos/<id>/update/ ────────────────────────────────────
@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_data(request, id):
    payment_method = get_object_or_404(PaymentMethod, id=id)

    serializer = PaymentMethodUpdateSerializer(payment_method, data=request.data, partial=True)
    if serializer.is_valid():
        if 'logo' in request.FILES and payment_method.logo:
            _delete_s3_image(payment_method.logo)
        serializer.save()
        return Response(PaymentMethodDetailSerializer(payment_method).data, status=status.HTTP_200_OK)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ── DELETE /api/metodos-pagos/<id>/image/logo/ ─────────────────────────────
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_logo(request, id):
    payment_method = get_object_or_404(PaymentMethod, id=id)

    if not payment_method.logo:
        return Response({'detail': 'This payment method has no logo.'}, status=status.HTTP_404_NOT_FOUND)

    _delete_s3_image(payment_method.logo)
    payment_method.logo = None
    payment_method.save()
    return Response({'message': 'Logo deleted successfully.'}, status=status.HTTP_200_OK)


# ── DELETE /api/metodos-pagos/<id>/delete/ ─────────────────────────────────
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_data(request, id):
    payment_method = get_object_or_404(PaymentMethod, id=id)

    if payment_method.deleted_at is not None:
        return Response({'detail': 'Payment method is already deleted.'}, status=status.HTTP_400_BAD_REQUEST)

    payment_method.deleted_at = timezone.now()
    payment_method.is_active  = False
    payment_method.save()
    return Response({'message': 'Payment method deleted successfully.'}, status=status.HTTP_200_OK)
