from rest_framework.decorators  import api_view, permission_classes
from django.shortcuts           import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination  import PageNumberPagination
from rest_framework.response    import Response
from rest_framework             import status
from django.utils               import timezone
from django.db.models           import Q
from tp_feature_area.models     import TpFeatureArea
from .serializers               import (
    TpFeatureAreaSerializer, TpFeatureAreaListSerializer,
    TpFeatureAreaDetailSerializer, TpFeatureAreaUpdateSerializer,
)


# ── POST /api/tp-feature-area/create/ ──────────────────────────────────────
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_data(request):
    serializer = TpFeatureAreaSerializer(data=request.data)
    if serializer.is_valid():
        feature = serializer.save(user=request.user)
        return Response(
            {'message': 'Feature created successfully.', 'data': TpFeatureAreaDetailSerializer(feature).data},
            status=status.HTTP_201_CREATED
        )
    return Response({'message': 'Invalid data.', 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


# ── GET /api/tp-feature-area/all/ ──────────────────────────────────────────
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_all_data(request):
    deleted_param = request.GET.get('deleted', 'false')
    if deleted_param.lower() == 'true':
        features = TpFeatureArea.objects.filter(deleted_at__isnull=False)
    else:
        features = TpFeatureArea.objects.filter(deleted_at__isnull=True)

    search = request.GET.get('search', None)
    if search:
        features = features.filter(
            Q(title__icontains=search) |
            Q(description__icontains=search)
        )

    paginator = PageNumberPagination()
    paginator.page_size             = 10
    paginator.page_size_query_param = 'page_size'
    paginator.max_page_size         = 100

    result_page = paginator.paginate_queryset(features, request)
    serializer  = TpFeatureAreaListSerializer(result_page, many=True)
    return paginator.get_paginated_response(serializer.data)


# ── GET /api/tp-feature-area/<id>/ ─────────────────────────────────────────
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_by_id(request, id):
    feature    = get_object_or_404(TpFeatureArea, id=id)
    serializer = TpFeatureAreaDetailSerializer(feature)
    return Response(serializer.data, status=status.HTTP_200_OK)


# ── PUT /api/tp-feature-area/<id>/update/ ──────────────────────────────────
@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_data(request, id):
    feature = get_object_or_404(TpFeatureArea, id=id)

    serializer = TpFeatureAreaUpdateSerializer(feature, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(TpFeatureAreaDetailSerializer(feature).data, status=status.HTTP_200_OK)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ── DELETE /api/tp-feature-area/<id>/delete/ ───────────────────────────────
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_data(request, id):
    feature = get_object_or_404(TpFeatureArea, id=id)

    if feature.deleted_at is not None:
        return Response({'detail': 'Feature is already deleted.'}, status=status.HTTP_400_BAD_REQUEST)

    feature.deleted_at = timezone.now()
    feature.save()
    return Response({'message': 'Feature deleted successfully.'}, status=status.HTTP_200_OK)
