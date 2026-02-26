from rest_framework.decorators  import api_view, permission_classes
from django.shortcuts           import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination  import PageNumberPagination
from rest_framework.response    import Response
from rest_framework             import status
from django.core.files.storage  import default_storage
from django.utils               import timezone
from django.db.models           import Q
from category.models            import Category
from .serializers               import (
    CategorySerializer, CategoryListSerializer,
    CategoryDetailSerializer, CategoryUpdateSerializer,
)


def _delete_s3_image(image_field):
    """Elimina el archivo de S3 asociado a un ImageField. Silencia errores."""
    if image_field:
        try:
            default_storage.delete(image_field.name)
        except Exception:
            pass


# ── POST /api/category/create/ ───────────────────────────────────────────────
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_data(request):
    serializer = CategorySerializer(data=request.data)
    if serializer.is_valid():
        category = serializer.save(user=request.user)
        return Response(
            {'message': 'Category created successfully.', 'data': CategoryDetailSerializer(category).data},
            status=status.HTTP_201_CREATED
        )
    return Response({'message': 'Invalid data.', 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


# ── GET /api/category/all/ ───────────────────────────────────────────────────
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_all_data(request):
    # Por defecto solo muestra no eliminadas; ?deleted=true muestra las eliminadas
    deleted_param = request.GET.get('deleted', 'false')
    if deleted_param.lower() == 'true':
        categories = Category.objects.filter(deleted_at__isnull=False)
    else:
        categories = Category.objects.filter(deleted_at__isnull=True)

    search = request.GET.get('search', None)
    if search:
        categories = categories.filter(
            Q(name__icontains=search) |
            Q(slug__icontains=search)
        )

    if is_active := request.GET.get('is_active', None):
        if is_active.lower() == 'true':
            categories = categories.filter(is_active=True)
        elif is_active.lower() == 'false':
            categories = categories.filter(is_active=False)

    paginator = PageNumberPagination()
    paginator.page_size             = 10
    paginator.page_size_query_param = 'page_size'
    paginator.max_page_size         = 100

    result_page = paginator.paginate_queryset(categories, request)
    serializer  = CategoryListSerializer(result_page, many=True)
    return paginator.get_paginated_response(serializer.data)


# ── GET /api/category/<id>/ ──────────────────────────────────────────────────
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_by_id(request, id):
    category   = get_object_or_404(Category, id=id)
    serializer = CategoryDetailSerializer(category)
    return Response(serializer.data, status=status.HTTP_200_OK)


# ── PUT /api/category/<id>/update/ ───────────────────────────────────────────
@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_data(request, id):
    category = get_object_or_404(Category, id=id)

    serializer = CategoryUpdateSerializer(category, data=request.data, partial=True)
    if serializer.is_valid():
        if 'image' in request.FILES and category.image:
            _delete_s3_image(category.image)
        serializer.save(updated_by=request.user)
        return Response(CategoryDetailSerializer(category).data, status=status.HTTP_200_OK)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ── DELETE /api/category/<id>/image/ ─────────────────────────────────────────
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_image(request, id):
    category = get_object_or_404(Category, id=id)

    if not category.image:
        return Response({'detail': 'This category has no image.'}, status=status.HTTP_404_NOT_FOUND)

    _delete_s3_image(category.image)
    category.image      = None
    category.updated_by = request.user
    category.save()
    return Response({'message': 'Category image deleted successfully.'}, status=status.HTTP_200_OK)


# ── DELETE /api/category/<id>/delete/ ────────────────────────────────────────
# Soft delete: nunca se elimina, solo se registra la fecha y quién lo hizo
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_data(request, id):
    category = get_object_or_404(Category, id=id)

    if category.deleted_at is not None:
        return Response({'detail': 'Category is already deleted.'}, status=status.HTTP_400_BAD_REQUEST)

    category.deleted_at = timezone.now()
    category.deleted_by = request.user
    category.is_active  = False
    category.save()
    return Response({'message': 'Category deleted successfully.'}, status=status.HTTP_200_OK)
