from rest_framework.decorators  import api_view, permission_classes
from django.shortcuts           import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination  import PageNumberPagination
from rest_framework.response    import Response
from rest_framework             import status
from django.core.files.storage  import default_storage
from django.utils               import timezone
from django.db.models           import Q
from slider.models              import Slider
from .serializers               import (
    SliderSerializer, SliderListSerializer,
    SliderDetailSerializer, SliderUpdateSerializer,
)


def _delete_s3_image(image_field):
    """Elimina el archivo de S3 asociado a un ImageField. Silencia errores."""
    if image_field:
        try:
            default_storage.delete(image_field.name)
        except Exception:
            pass


# ── POST /api/slider/create/ ────────────────────────────────────────────────
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_data(request):
    serializer = SliderSerializer(data=request.data)
    if serializer.is_valid():
        slider = serializer.save(user=request.user)
        return Response(
            {'message': 'Slider created successfully.', 'data': SliderDetailSerializer(slider).data},
            status=status.HTTP_201_CREATED
        )
    return Response({'message': 'Invalid data.', 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


# ── GET /api/slider/all/ ────────────────────────────────────────────────────
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_all_data(request):
    deleted_param = request.GET.get('deleted', 'false')
    if deleted_param.lower() == 'true':
        sliders = Slider.objects.filter(deleted_at__isnull=False)
    else:
        sliders = Slider.objects.filter(deleted_at__isnull=True)

    search = request.GET.get('search', None)
    if search:
        sliders = sliders.filter(
            Q(title__icontains=search) |
            Q(subtitle__icontains=search)
        )

    if is_active := request.GET.get('is_active', None):
        if is_active.lower() == 'true':
            sliders = sliders.filter(is_active=True)
        elif is_active.lower() == 'false':
            sliders = sliders.filter(is_active=False)

    paginator = PageNumberPagination()
    paginator.page_size             = 10
    paginator.page_size_query_param = 'page_size'
    paginator.max_page_size         = 100

    result_page = paginator.paginate_queryset(sliders, request)
    serializer  = SliderListSerializer(result_page, many=True)
    return paginator.get_paginated_response(serializer.data)


# ── GET /api/slider/<id>/ ───────────────────────────────────────────────────
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_by_id(request, id):
    slider     = get_object_or_404(Slider, id=id)
    serializer = SliderDetailSerializer(slider)
    return Response(serializer.data, status=status.HTTP_200_OK)


# ── PUT /api/slider/<id>/update/ ────────────────────────────────────────────
@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_data(request, id):
    slider = get_object_or_404(Slider, id=id)

    serializer = SliderUpdateSerializer(slider, data=request.data, partial=True)
    if serializer.is_valid():
        if 'custom_image' in request.FILES and slider.custom_image:
            _delete_s3_image(slider.custom_image)
        serializer.save(updated_by=request.user)
        return Response(SliderDetailSerializer(slider).data, status=status.HTTP_200_OK)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ── DELETE /api/slider/<id>/image/ ──────────────────────────────────────────
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_image(request, id):
    slider = get_object_or_404(Slider, id=id)

    if not slider.custom_image:
        return Response({'detail': 'This slider has no custom image.'}, status=status.HTTP_404_NOT_FOUND)

    _delete_s3_image(slider.custom_image)
    slider.custom_image = None
    slider.updated_by   = request.user
    slider.save()
    return Response({'message': 'Slider image deleted successfully.'}, status=status.HTTP_200_OK)


# ── DELETE /api/slider/<id>/delete/ ─────────────────────────────────────────
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_data(request, id):
    slider = get_object_or_404(Slider, id=id)

    if slider.deleted_at is not None:
        return Response({'detail': 'Slider is already deleted.'}, status=status.HTTP_400_BAD_REQUEST)

    slider.deleted_at = timezone.now()
    slider.deleted_by = request.user
    slider.is_active  = False
    slider.save()
    return Response({'message': 'Slider deleted successfully.'}, status=status.HTTP_200_OK)
