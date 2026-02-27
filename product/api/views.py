from rest_framework.decorators  import api_view, permission_classes
from django.shortcuts           import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination  import PageNumberPagination
from rest_framework.response    import Response
from rest_framework             import status
from django.utils               import timezone
from django.db.models           import Q, Max
from product.models             import Product, ProductImage, ProductVariant
from .serializers               import (
    ProductSerializer, ProductListSerializer,
    ProductDetailSerializer, ProductUpdateSerializer,
    ProductImageSerializer,
    ProductVariantSerializer, ProductVariantListSerializer,
    ProductVariantDetailSerializer, ProductVariantUpdateSerializer,
)


# ── POST /api/product/create/ ────────────────────────────────────────────────
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_data(request):
    serializer = ProductSerializer(data=request.data)
    if serializer.is_valid():
        product = serializer.save(user=request.user)
        return Response(
            {'message': 'Product created successfully.', 'data': ProductDetailSerializer(product, context={'request': request}).data},
            status=status.HTTP_201_CREATED
        )
    return Response({'message': 'Invalid data.', 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


# ── GET /api/product/all/ ─────────────────────────────────────────────────────
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_all_data(request):
    deleted_param = request.GET.get('deleted', 'false')
    if deleted_param.lower() == 'true':
        products = Product.objects.filter(deleted_at__isnull=False)
    else:
        products = Product.objects.filter(deleted_at__isnull=True)

    category_id = request.GET.get('category_id', None)
    if category_id:
        products = products.filter(category_id=category_id)

    is_active = request.GET.get('is_active', None)
    if is_active is not None:
        products = products.filter(is_active=is_active.lower() == 'true')

    is_featured = request.GET.get('is_featured', None)
    if is_featured is not None:
        products = products.filter(is_featured=is_featured.lower() == 'true')

    search = request.GET.get('search', None)
    if search:
        products = products.filter(
            Q(name__icontains=search) |
            Q(sku__icontains=search)  |
            Q(slug__icontains=search)
        )

    paginator = PageNumberPagination()
    paginator.page_size             = 10
    paginator.page_size_query_param = 'page_size'
    paginator.max_page_size         = 100

    result_page = paginator.paginate_queryset(products, request)
    serializer  = ProductListSerializer(result_page, many=True, context={'request': request})
    return paginator.get_paginated_response(serializer.data)


# ── GET /api/product/<id>/ ────────────────────────────────────────────────────
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_by_id(request, id):
    product    = get_object_or_404(Product, id=id)
    serializer = ProductDetailSerializer(product, context={'request': request})
    return Response(serializer.data, status=status.HTTP_200_OK)


# ── PUT /api/product/<id>/update/ ─────────────────────────────────────────────
@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_data(request, id):
    product    = get_object_or_404(Product, id=id)
    serializer = ProductUpdateSerializer(product, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save(updated_by=request.user)
        return Response(ProductDetailSerializer(product, context={'request': request}).data, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ── DELETE /api/product/<id>/delete/ ──────────────────────────────────────────
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_data(request, id):
    product = get_object_or_404(Product, id=id)

    if product.deleted_at is not None:
        return Response({'detail': 'Product is already deleted.'}, status=status.HTTP_400_BAD_REQUEST)

    product.deleted_at = timezone.now()
    product.deleted_by = request.user
    product.save()
    return Response({'message': 'Product deleted successfully.'}, status=status.HTTP_200_OK)


# ── POST /api/product/<id>/images/upload/ ─────────────────────────────────────
# Acepta uno o varios archivos en el campo 'images' (multipart/form-data).
# Las imágenes se añaden a la galería del producto respetando el orden actual.
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upload_images(request, id):
    product = get_object_or_404(Product, id=id)
    files   = request.FILES.getlist('images')

    if not files:
        return Response(
            {'message': 'No se enviaron imágenes. Usa el campo "images" como multipart.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Continúa desde el último order registrado
    last_order = product.images.aggregate(Max('order'))['order__max'] or -1

    for i, file in enumerate(files):
        ProductImage.objects.create(
            product=product,
            image=file,
            order=last_order + i + 1,
        )

    serializer = ProductImageSerializer(
        product.images.all(), many=True, context={'request': request}
    )
    return Response({'images': serializer.data}, status=status.HTTP_201_CREATED)


# ── DELETE /api/product/images/<image_id>/delete/ ─────────────────────────────
# Elimina una sola imagen de la galería (también borra el archivo en storage).
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_image(request, image_id):
    img = get_object_or_404(ProductImage, id=image_id)
    img.image.delete(save=False)   # elimina el archivo de S3 / filesystem
    img.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


# ── PUT /api/product/<id>/images/reorder/ ─────────────────────────────────────
# Body: { "order": [image_id_1, image_id_2, ...] }
# Actualiza el campo 'order' de cada ProductImage según la posición en el array.
@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def reorder_images(request, id):
    product    = get_object_or_404(Product, id=id)
    order_list = request.data.get('order', [])

    if not order_list:
        return Response(
            {'message': 'El campo "order" es requerido (lista de IDs de imagen).'},
            status=status.HTTP_400_BAD_REQUEST
        )

    for position, image_id in enumerate(order_list):
        ProductImage.objects.filter(id=image_id, product=product).update(order=position)

    serializer = ProductImageSerializer(
        product.images.all(), many=True, context={'request': request}
    )
    return Response({'images': serializer.data}, status=status.HTTP_200_OK)


# ═══════════════════════════════════════════════════════════════════════════════
# VARIANTES
# ═══════════════════════════════════════════════════════════════════════════════

# ── POST /api/product/<id>/variants/create/ ────────────────────────────────────
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_variant(request, id):
    product = get_object_or_404(Product, id=id)
    serializer = ProductVariantSerializer(data=request.data)
    if serializer.is_valid():
        variant = serializer.save(user=request.user, product=product)
        return Response(
            {
                'message': 'Variante creada correctamente.',
                'data': ProductVariantDetailSerializer(variant, context={'request': request}).data,
            },
            status=status.HTTP_201_CREATED,
        )
    return Response({'message': 'Datos inválidos.', 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


# ── GET /api/product/<id>/variants/ ───────────────────────────────────────────
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_variants(request, id):
    product  = get_object_or_404(Product, id=id)
    variants = product.variants.filter(deleted_at__isnull=True)

    is_active = request.GET.get('is_active')
    if is_active is not None:
        variants = variants.filter(is_active=is_active.lower() == 'true')

    serializer = ProductVariantListSerializer(variants, many=True, context={'request': request})
    return Response(serializer.data, status=status.HTTP_200_OK)


# ── GET /api/product/variants/<variant_id>/ ────────────────────────────────────
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_variant_by_id(request, variant_id):
    variant    = get_object_or_404(ProductVariant, id=variant_id)
    serializer = ProductVariantDetailSerializer(variant, context={'request': request})
    return Response(serializer.data, status=status.HTTP_200_OK)


# ── PUT /api/product/variants/<variant_id>/update/ ────────────────────────────
@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_variant(request, variant_id):
    variant    = get_object_or_404(ProductVariant, id=variant_id)
    serializer = ProductVariantUpdateSerializer(variant, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(
            ProductVariantDetailSerializer(variant, context={'request': request}).data,
            status=status.HTTP_200_OK,
        )
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ── DELETE /api/product/variants/<variant_id>/delete/ ─────────────────────────
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_variant(request, variant_id):
    variant = get_object_or_404(ProductVariant, id=variant_id)

    if variant.deleted_at is not None:
        return Response({'detail': 'La variante ya está eliminada.'}, status=status.HTTP_400_BAD_REQUEST)

    variant.deleted_at = timezone.now()
    variant.save()
    return Response({'message': 'Variante eliminada correctamente.'}, status=status.HTTP_200_OK)
