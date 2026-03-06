from rest_framework.decorators  import api_view, permission_classes
from django.shortcuts           import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination  import PageNumberPagination
from rest_framework.response    import Response
from rest_framework             import status
from django.utils               import timezone
from django.db.models           import Q
from customer.models            import Customer, CustomerAddress
from .serializers               import (
    CustomerSerializer, CustomerListSerializer,
    CustomerDetailSerializer, CustomerUpdateSerializer,
    CustomerAddressCreateSerializer, CustomerAddressSerializer,
)


# ── POST /api/customer/create/ ───────────────────────────────────────────────
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_data(request):
    serializer = CustomerSerializer(data=request.data)
    if serializer.is_valid():
        customer = serializer.save()
        return Response(
            {'message': 'Customer created successfully.', 'data': CustomerDetailSerializer(customer).data},
            status=status.HTTP_201_CREATED
        )
    return Response({'message': 'Invalid data.', 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


# ── GET /api/customer/all/ ───────────────────────────────────────────────────
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_all_data(request):
    deleted_param = request.GET.get('deleted', 'false')
    if deleted_param.lower() == 'true':
        customers = Customer.objects.filter(deleted_at__isnull=False)
    else:
        customers = Customer.objects.filter(deleted_at__isnull=True)

    search = request.GET.get('search', None)
    if search:
        customers = customers.filter(
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search) |
            Q(email__icontains=search) |
            Q(document_number__icontains=search)
        )

    if is_active := request.GET.get('is_active', None):
        if is_active.lower() == 'true':
            customers = customers.filter(is_active=True)
        elif is_active.lower() == 'false':
            customers = customers.filter(is_active=False)

    if gender_id := request.GET.get('gender_id', None):
        customers = customers.filter(gender_id=gender_id)

    paginator = PageNumberPagination()
    paginator.page_size             = 10
    paginator.page_size_query_param = 'page_size'
    paginator.max_page_size         = 100

    result_page = paginator.paginate_queryset(customers, request)
    serializer  = CustomerListSerializer(result_page, many=True)
    return paginator.get_paginated_response(serializer.data)


# ── GET /api/customer/<id>/ ──────────────────────────────────────────────────
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_by_id(request, id):
    customer   = get_object_or_404(Customer, id=id)
    serializer = CustomerDetailSerializer(customer)
    return Response(serializer.data, status=status.HTTP_200_OK)


# ── PUT /api/customer/<id>/update/ ───────────────────────────────────────────
@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_data(request, id):
    customer = get_object_or_404(Customer, id=id)

    serializer = CustomerUpdateSerializer(customer, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(CustomerDetailSerializer(customer).data, status=status.HTTP_200_OK)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ── DELETE /api/customer/<id>/delete/ ────────────────────────────────────────
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_data(request, id):
    customer = get_object_or_404(Customer, id=id)

    if customer.deleted_at is not None:
        return Response({'detail': 'Customer is already deleted.'}, status=status.HTTP_400_BAD_REQUEST)

    customer.deleted_at = timezone.now()
    customer.is_active  = False
    customer.save()
    return Response({'message': 'Customer deleted successfully.'}, status=status.HTTP_200_OK)


# ═══════════════════════════════════════════════════════════════════════════════
# Direcciones del cliente
# ═══════════════════════════════════════════════════════════════════════════════

# ── POST /api/customer/<id>/address/create/ ──────────────────────────────────
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_address(request, id):
    customer = get_object_or_404(Customer, id=id)
    serializer = CustomerAddressCreateSerializer(data=request.data)
    if serializer.is_valid():
        address = serializer.save(customer=customer)
        return Response(
            {'message': 'Address created successfully.', 'data': CustomerAddressSerializer(address).data},
            status=status.HTTP_201_CREATED
        )
    return Response({'message': 'Invalid data.', 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


# ── PUT /api/customer/address/<id>/update/ ───────────────────────────────────
@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_address(request, id):
    address = get_object_or_404(CustomerAddress, id=id)
    serializer = CustomerAddressCreateSerializer(address, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(CustomerAddressSerializer(address).data, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ── DELETE /api/customer/address/<id>/delete/ ────────────────────────────────
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_address(request, id):
    address = get_object_or_404(CustomerAddress, id=id)
    address.delete()
    return Response({'message': 'Address deleted successfully.'}, status=status.HTTP_200_OK)
