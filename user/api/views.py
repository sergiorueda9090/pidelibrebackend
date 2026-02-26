from rest_framework.decorators  import api_view, permission_classes
from django.shortcuts           import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination  import PageNumberPagination
from rest_framework.response    import Response
from rest_framework             import status
from django.core.files.storage  import default_storage
from user.models                import User
from .serializers               import UserSerializer, UserListSerializer, UserDetailSerializer, UserUpdateSerializer
from django.db.models           import Q


def _delete_s3_image(image_field):
    """Elimina el archivo de S3 asociado a un ImageField. Silencia errores."""
    if image_field:
        try:
            default_storage.delete(image_field.name)
        except Exception:
            pass


# ── GET /api/user/me/ ────────────────────────────────────────────────────────
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def me(request):
    user = request.user
    return Response({
        'id':            user.id,
        'username':      user.username,
        'email':         user.email,
        'first_name':    user.first_name,
        'last_name':     user.last_name,
        'profile_image': user.profile_image.url if user.profile_image else None,
    })


# ── POST /api/user/create/ ───────────────────────────────────────────────────
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_data(request):
    serializer = UserSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        return Response(
            {'message': 'User created successfully.', 'data': UserDetailSerializer(user).data},
            status=status.HTTP_201_CREATED
        )
    return Response({'message': 'Invalid data.', 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


# ── GET /api/user/all/ ───────────────────────────────────────────────────────
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_all_data(request):
    users = User.objects.all().order_by('id')
    search = request.GET.get('search', None)
    if search:
        users = users.filter(
            Q(username__icontains=search)   |
            Q(email__icontains=search)      |
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search)
        )

    start_date = request.GET.get('start_date', None)
    end_date   = request.GET.get('end_date',   None)

    if start_date:
        users = users.filter(date_joined__date__gte=start_date)
    if end_date:
        users = users.filter(date_joined__date__lte=end_date)

    if is_active := request.GET.get('is_active', None):
        if is_active.lower() == 'true':
            users = users.filter(is_active=True)
        elif is_active.lower() == 'false':
            users = users.filter(is_active=False)

    paginator = PageNumberPagination()
    paginator.page_size             = 10
    paginator.page_size_query_param = 'page_size'
    paginator.max_page_size         = 100

    result_page = paginator.paginate_queryset(users, request)
    serializer  = UserListSerializer(result_page, many=True)
    return paginator.get_paginated_response(serializer.data)


# ── GET /api/user/<id>/ ──────────────────────────────────────────────────────
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_by_id(request, id):
    user       = get_object_or_404(User, id=id)
    serializer = UserDetailSerializer(user)
    return Response(serializer.data, status=status.HTTP_200_OK)


# ── PUT /api/user/<id>/update/ ───────────────────────────────────────────────
@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_data(request, id):
    user = get_object_or_404(User, id=id)

    if not request.user.is_staff and request.user.id != user.id:
        return Response({'detail': 'You do not have permission.'}, status=status.HTTP_403_FORBIDDEN)

    serializer = UserUpdateSerializer(user, data=request.data, partial=True)
    if serializer.is_valid():
        # Si llega imagen nueva, borrar la anterior de S3
        if 'profile_image' in request.FILES and user.profile_image:
            _delete_s3_image(user.profile_image)
        serializer.save()
        return Response(UserDetailSerializer(user).data, status=status.HTTP_200_OK)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ── DELETE /api/user/<id>/image/ ─────────────────────────────────────────────
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_image(request, id):
    user = get_object_or_404(User, id=id)

    if not request.user.is_staff and request.user.id != user.id:
        return Response({'detail': 'You do not have permission.'}, status=status.HTTP_403_FORBIDDEN)

    if not user.profile_image:
        return Response({'detail': 'This user has no profile image.'}, status=status.HTTP_404_NOT_FOUND)

    _delete_s3_image(user.profile_image)
    user.profile_image = None
    user.save()
    return Response({'message': 'Profile image deleted successfully.'}, status=status.HTTP_200_OK)


# ── DELETE /api/user/<id>/delete/ ────────────────────────────────────────────
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_data(request, id):
    user = get_object_or_404(User, id=id)

    if not request.user.is_staff and request.user.id != user.id:
        return Response({'detail': 'You do not have permission to delete this user.'}, status=status.HTTP_403_FORBIDDEN)

    _delete_s3_image(user.profile_image)
    user.delete()
    return Response({'message': 'User deleted successfully.'}, status=status.HTTP_204_NO_CONTENT)
