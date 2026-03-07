from rest_framework.decorators  import api_view, permission_classes
from django.shortcuts           import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination  import PageNumberPagination
from rest_framework.response    import Response
from rest_framework             import status
from django.core.files.storage  import default_storage
from django.utils               import timezone
from django.db.models           import Q
from footer.models              import Footer
from .serializers               import (
    FooterSerializer, FooterListSerializer,
    FooterDetailSerializer, FooterUpdateSerializer,
)


def _delete_s3_image(image_field):
    """Elimina el archivo de S3 asociado a un ImageField. Silencia errores."""
    if image_field:
        try:
            default_storage.delete(image_field.name)
        except Exception:
            pass


# ── POST /api/footer/create/ ──────────────────────────────────────────────
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_data(request):
    serializer = FooterSerializer(data=request.data)
    if serializer.is_valid():
        footer = serializer.save(user=request.user)
        return Response(
            {'message': 'Footer created successfully.', 'data': FooterDetailSerializer(footer).data},
            status=status.HTTP_201_CREATED
        )
    return Response({'message': 'Invalid data.', 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


# ── GET /api/footer/all/ ──────────────────────────────────────────────────
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_all_data(request):
    deleted_param = request.GET.get('deleted', 'false')
    if deleted_param.lower() == 'true':
        footers = Footer.objects.filter(deleted_at__isnull=False)
    else:
        footers = Footer.objects.filter(deleted_at__isnull=True)

    search = request.GET.get('search', None)
    if search:
        footers = footers.filter(
            Q(description__icontains=search) |
            Q(phone__icontains=search) |
            Q(email__icontains=search)
        )

    paginator = PageNumberPagination()
    paginator.page_size             = 10
    paginator.page_size_query_param = 'page_size'
    paginator.max_page_size         = 100

    result_page = paginator.paginate_queryset(footers, request)
    serializer  = FooterListSerializer(result_page, many=True)
    return paginator.get_paginated_response(serializer.data)


# ── GET /api/footer/<id>/ ─────────────────────────────────────────────────
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_by_id(request, id):
    footer     = get_object_or_404(Footer, id=id)
    serializer = FooterDetailSerializer(footer)
    return Response(serializer.data, status=status.HTTP_200_OK)


# ── PUT /api/footer/<id>/update/ ──────────────────────────────────────────
@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_data(request, id):
    footer = get_object_or_404(Footer, id=id)

    serializer = FooterUpdateSerializer(footer, data=request.data, partial=True)
    if serializer.is_valid():
        if 'logo' in request.FILES and footer.logo:
            _delete_s3_image(footer.logo)
        if 'payment_image' in request.FILES and footer.payment_image:
            _delete_s3_image(footer.payment_image)
        serializer.save()
        return Response(FooterDetailSerializer(footer).data, status=status.HTTP_200_OK)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ── DELETE /api/footer/<id>/image/logo/ ───────────────────────────────────
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_logo(request, id):
    footer = get_object_or_404(Footer, id=id)

    if not footer.logo:
        return Response({'detail': 'This footer has no logo.'}, status=status.HTTP_404_NOT_FOUND)

    _delete_s3_image(footer.logo)
    footer.logo = None
    footer.save()
    return Response({'message': 'Logo deleted successfully.'}, status=status.HTTP_200_OK)


# ── DELETE /api/footer/<id>/image/payment/ ────────────────────────────────
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_payment_image(request, id):
    footer = get_object_or_404(Footer, id=id)

    if not footer.payment_image:
        return Response({'detail': 'This footer has no payment image.'}, status=status.HTTP_404_NOT_FOUND)

    _delete_s3_image(footer.payment_image)
    footer.payment_image = None
    footer.save()
    return Response({'message': 'Payment image deleted successfully.'}, status=status.HTTP_200_OK)


# ── DELETE /api/footer/<id>/delete/ ───────────────────────────────────────
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_data(request, id):
    footer = get_object_or_404(Footer, id=id)

    if footer.deleted_at is not None:
        return Response({'detail': 'Footer is already deleted.'}, status=status.HTTP_400_BAD_REQUEST)

    footer.deleted_at = timezone.now()
    footer.is_active  = False
    footer.save()
    return Response({'message': 'Footer deleted successfully.'}, status=status.HTTP_200_OK)
