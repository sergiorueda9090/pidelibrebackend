from rest_framework.decorators  import api_view, permission_classes
from django.shortcuts           import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination  import PageNumberPagination
from rest_framework.response    import Response
from rest_framework             import status
from django.utils               import timezone
from django.db.models           import Q
from attribute_value.models     import AttributeValue
from .serializers               import (
    AttributeValueSerializer, AttributeValueListSerializer,
    AttributeValueDetailSerializer, AttributeValueUpdateSerializer,
)


# ── POST /api/attribute-value/create/ ────────────────────────────────────────
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_data(request):
    serializer = AttributeValueSerializer(data=request.data)
    if serializer.is_valid():
        attr_value = serializer.save(user=request.user)
        return Response(
            {'message': 'Attribute value created successfully.', 'data': AttributeValueDetailSerializer(attr_value).data},
            status=status.HTTP_201_CREATED
        )
    return Response({'message': 'Invalid data.', 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


# ── GET /api/attribute-value/all/ ─────────────────────────────────────────────
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_all_data(request):
    # Por defecto solo muestra no eliminados; ?deleted=true muestra los eliminados
    deleted_param = request.GET.get('deleted', 'false')
    if deleted_param.lower() == 'true':
        values = AttributeValue.objects.filter(deleted_at__isnull=False)
    else:
        values = AttributeValue.objects.filter(deleted_at__isnull=True)

    # Filtrar por atributo padre: ?attribute_id=<id>
    attribute_id = request.GET.get('attribute_id', None)
    if attribute_id:
        values = values.filter(attribute_id=attribute_id)

    search = request.GET.get('search', None)
    if search:
        values = values.filter(
            Q(value__icontains=search) |
            Q(attribute__name__icontains=search)
        )

    paginator = PageNumberPagination()
    paginator.page_size             = 10
    paginator.page_size_query_param = 'page_size'
    paginator.max_page_size         = 100

    result_page = paginator.paginate_queryset(values, request)
    serializer  = AttributeValueListSerializer(result_page, many=True)
    return paginator.get_paginated_response(serializer.data)


# ── GET /api/attribute-value/<id>/ ────────────────────────────────────────────
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_by_id(request, id):
    attr_value = get_object_or_404(AttributeValue, id=id)
    serializer = AttributeValueDetailSerializer(attr_value)
    return Response(serializer.data, status=status.HTTP_200_OK)


# ── PUT /api/attribute-value/<id>/update/ ─────────────────────────────────────
@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_data(request, id):
    attr_value = get_object_or_404(AttributeValue, id=id)
    serializer = AttributeValueUpdateSerializer(attr_value, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(AttributeValueDetailSerializer(attr_value).data, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ── DELETE /api/attribute-value/<id>/delete/ ──────────────────────────────────
# Soft delete: nunca se elimina, solo se registra la fecha
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_data(request, id):
    attr_value = get_object_or_404(AttributeValue, id=id)

    if attr_value.deleted_at is not None:
        return Response({'detail': 'Attribute value is already deleted.'}, status=status.HTTP_400_BAD_REQUEST)

    attr_value.deleted_at = timezone.now()
    attr_value.save()
    return Response({'message': 'Attribute value deleted successfully.'}, status=status.HTTP_200_OK)
