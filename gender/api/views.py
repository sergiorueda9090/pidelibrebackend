from rest_framework.decorators  import api_view, permission_classes
from django.shortcuts           import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination  import PageNumberPagination
from rest_framework.response    import Response
from rest_framework             import status
from django.utils               import timezone
from django.db.models           import Q
from gender.models              import Gender
from .serializers               import (
    GenderSerializer, GenderListSerializer,
    GenderDetailSerializer, GenderUpdateSerializer,
)


# ── POST /api/gender/create/ ─────────────────────────────────────────────────
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_data(request):
    serializer = GenderSerializer(data=request.data)
    if serializer.is_valid():
        gender = serializer.save(user=request.user)
        return Response(
            {'message': 'Gender created successfully.', 'data': GenderDetailSerializer(gender).data},
            status=status.HTTP_201_CREATED
        )
    return Response({'message': 'Invalid data.', 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


# ── GET /api/gender/all/ ─────────────────────────────────────────────────────
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_all_data(request):
    deleted_param = request.GET.get('deleted', 'false')
    if deleted_param.lower() == 'true':
        genders = Gender.objects.filter(deleted_at__isnull=False)
    else:
        genders = Gender.objects.filter(deleted_at__isnull=True)

    search = request.GET.get('search', None)
    if search:
        genders = genders.filter(
            Q(name__icontains=search) |
            Q(slug__icontains=search)
        )

    paginator = PageNumberPagination()
    paginator.page_size             = 10
    paginator.page_size_query_param = 'page_size'
    paginator.max_page_size         = 100

    result_page = paginator.paginate_queryset(genders, request)
    serializer  = GenderListSerializer(result_page, many=True)
    return paginator.get_paginated_response(serializer.data)


# ── GET /api/gender/<id>/ ────────────────────────────────────────────────────
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_by_id(request, id):
    gender     = get_object_or_404(Gender, id=id)
    serializer = GenderDetailSerializer(gender)
    return Response(serializer.data, status=status.HTTP_200_OK)


# ── PUT /api/gender/<id>/update/ ─────────────────────────────────────────────
@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_data(request, id):
    gender = get_object_or_404(Gender, id=id)

    serializer = GenderUpdateSerializer(gender, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(GenderDetailSerializer(gender).data, status=status.HTTP_200_OK)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ── DELETE /api/gender/<id>/delete/ ──────────────────────────────────────────
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_data(request, id):
    gender = get_object_or_404(Gender, id=id)

    if gender.deleted_at is not None:
        return Response({'detail': 'Gender is already deleted.'}, status=status.HTTP_400_BAD_REQUEST)

    gender.deleted_at = timezone.now()
    gender.save()
    return Response({'message': 'Gender deleted successfully.'}, status=status.HTTP_200_OK)
