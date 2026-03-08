from rest_framework import serializers
from order.models import Order, OrderItem, Payment


class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = [
            'id', 'product_name', 'product_image', 'sku',
            'attributes', 'price', 'quantity', 'total',
        ]


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ['id', 'provider', 'transaction_id', 'status', 'amount', 'created_at']


class OrderDetailSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    payments = PaymentSerializer(many=True, read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Order
        fields = [
            'id', 'order_number', 'email', 'first_name', 'last_name',
            'phone', 'document_number', 'address', 'address2', 'city',
            'state', 'country', 'postal_code', 'notes', 'status',
            'status_display', 'payment_method', 'subtotal',
            'shipping_cost', 'total', 'created_at', 'items', 'payments',
        ]


class OrderListSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    items_count = serializers.IntegerField(source='items.count', read_only=True)

    class Meta:
        model = Order
        fields = [
            'id', 'order_number', 'email', 'first_name', 'last_name',
            'status', 'status_display', 'payment_method', 'total',
            'created_at', 'items_count',
        ]
