from rest_framework.decorators  import api_view, permission_classes
from django.shortcuts           import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination  import PageNumberPagination
from rest_framework.response    import Response
from rest_framework             import status
from django.core.files.storage  import default_storage
from django.utils               import timezone
from django.db.models           import Q
from brand.models               import Brand
from .serializers               import (
    BrandSerializer, BrandListSerializer,
    BrandDetailSerializer, BrandUpdateSerializer,
)


def _delete_s3_image(image_field):
    """Elimina el archivo de S3 asociado a un ImageField. Silencia errores."""
    if image_field:
        try:
            default_storage.delete(image_field.name)
        except Exception:
            pass


# ── POST /api/brand/create/ ──────────────────────────────────────────────────
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_data(request):
    serializer = BrandSerializer(data=request.data)
    if serializer.is_valid():
        brand = serializer.save(user=request.user)
        return Response(
            {'message': 'Brand created successfully.', 'data': BrandDetailSerializer(brand).data},
            status=status.HTTP_201_CREATED
        )
    return Response({'message': 'Invalid data.', 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


# ── GET /api/brand/all/ ──────────────────────────────────────────────────────
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_all_data(request):
    deleted_param = request.GET.get('deleted', 'false')
    if deleted_param.lower() == 'true':
        brands = Brand.objects.filter(deleted_at__isnull=False)
    else:
        brands = Brand.objects.filter(deleted_at__isnull=True)

    search = request.GET.get('search', None)
    if search:
        brands = brands.filter(
            Q(name__icontains=search) |
            Q(slug__icontains=search)
        )

    if is_active := request.GET.get('is_active', None):
        if is_active.lower() == 'true':
            brands = brands.filter(is_active=True)
        elif is_active.lower() == 'false':
            brands = brands.filter(is_active=False)

    paginator = PageNumberPagination()
    paginator.page_size             = 10
    paginator.page_size_query_param = 'page_size'
    paginator.max_page_size         = 100

    result_page = paginator.paginate_queryset(brands, request)
    serializer  = BrandListSerializer(result_page, many=True)
    return paginator.get_paginated_response(serializer.data)


# ── GET /api/brand/<id>/ ─────────────────────────────────────────────────────
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_by_id(request, id):
    brand      = get_object_or_404(Brand, id=id)
    serializer = BrandDetailSerializer(brand)
    return Response(serializer.data, status=status.HTTP_200_OK)


# ── PUT /api/brand/<id>/update/ ──────────────────────────────────────────────
@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_data(request, id):
    brand = get_object_or_404(Brand, id=id)

    serializer = BrandUpdateSerializer(brand, data=request.data, partial=True)
    if serializer.is_valid():
        if 'logo' in request.FILES and brand.logo:
            _delete_s3_image(brand.logo)
        serializer.save(updated_by=request.user)
        return Response(BrandDetailSerializer(brand).data, status=status.HTTP_200_OK)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ── DELETE /api/brand/<id>/logo/ ──────────────────────────────────────────────
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_logo(request, id):
    brand = get_object_or_404(Brand, id=id)

    if not brand.logo:
        return Response({'detail': 'This brand has no logo.'}, status=status.HTTP_404_NOT_FOUND)

    _delete_s3_image(brand.logo)
    brand.logo       = None
    brand.updated_by = request.user
    brand.save()
    return Response({'message': 'Brand logo deleted successfully.'}, status=status.HTTP_200_OK)


# ── DELETE /api/brand/<id>/delete/ ────────────────────────────────────────────
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_data(request, id):
    brand = get_object_or_404(Brand, id=id)

    if brand.deleted_at is not None:
        return Response({'detail': 'Brand is already deleted.'}, status=status.HTTP_400_BAD_REQUEST)

    brand.deleted_at = timezone.now()
    brand.deleted_by = request.user
    brand.is_active  = False
    brand.save()
    return Response({'message': 'Brand deleted successfully.'}, status=status.HTTP_200_OK)
