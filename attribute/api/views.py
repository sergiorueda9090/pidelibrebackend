from rest_framework.decorators  import api_view, permission_classes
from django.shortcuts           import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination  import PageNumberPagination
from rest_framework.response    import Response
from rest_framework             import status
from django.utils               import timezone
from django.db.models           import Q
from attribute.models           import Attribute
from .serializers               import (
    AttributeSerializer, AttributeListSerializer,
    AttributeDetailSerializer, AttributeUpdateSerializer,
)


# ── POST /api/attribute/create/ ──────────────────────────────────────────────
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_data(request):
    serializer = AttributeSerializer(data=request.data)
    if serializer.is_valid():
        attribute = serializer.save(user=request.user)
        return Response(
            {'message': 'Attribute created successfully.', 'data': AttributeDetailSerializer(attribute).data},
            status=status.HTTP_201_CREATED
        )
    return Response({'message': 'Invalid data.', 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


# ── GET /api/attribute/all/ ───────────────────────────────────────────────────
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_all_data(request):
    # Por defecto solo muestra no eliminadas; ?deleted=true muestra las eliminadas
    deleted_param = request.GET.get('deleted', 'false')
    if deleted_param.lower() == 'true':
        attributes = Attribute.objects.filter(deleted_at__isnull=False)
    else:
        attributes = Attribute.objects.filter(deleted_at__isnull=True)

    search = request.GET.get('search', None)
    if search:
        attributes = attributes.filter(Q(name__icontains=search))

    paginator = PageNumberPagination()
    paginator.page_size             = 10
    paginator.page_size_query_param = 'page_size'
    paginator.max_page_size         = 100

    result_page = paginator.paginate_queryset(attributes, request)
    serializer  = AttributeListSerializer(result_page, many=True)
    return paginator.get_paginated_response(serializer.data)


# ── GET /api/attribute/<id>/ ──────────────────────────────────────────────────
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_by_id(request, id):
    attribute  = get_object_or_404(Attribute, id=id)
    serializer = AttributeDetailSerializer(attribute)
    return Response(serializer.data, status=status.HTTP_200_OK)


# ── PUT /api/attribute/<id>/update/ ──────────────────────────────────────────
@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_data(request, id):
    attribute  = get_object_or_404(Attribute, id=id)
    serializer = AttributeUpdateSerializer(attribute, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(AttributeDetailSerializer(attribute).data, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ── DELETE /api/attribute/<id>/delete/ ────────────────────────────────────────
# Soft delete: nunca se elimina, solo se registra la fecha
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_data(request, id):
    attribute = get_object_or_404(Attribute, id=id)

    if attribute.deleted_at is not None:
        return Response({'detail': 'Attribute is already deleted.'}, status=status.HTTP_400_BAD_REQUEST)

    attribute.deleted_at = timezone.now()
    attribute.save()
    return Response({'message': 'Attribute deleted successfully.'}, status=status.HTTP_200_OK)
