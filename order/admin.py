from django.contrib import admin
from .models import Order, OrderItem, Payment, WebhookLog


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['product_name', 'product_image', 'sku', 'price', 'quantity', 'total']


class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 0
    readonly_fields = ['provider', 'transaction_id', 'status', 'amount', 'created_at']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_number', 'first_name', 'last_name', 'email', 'status', 'total', 'payment_method', 'created_at']
    list_filter = ['status', 'payment_method', 'created_at']
    search_fields = ['order_number', 'email', 'first_name', 'last_name']
    readonly_fields = ['order_number', 'created_at', 'updated_at']
    inlines = [OrderItemInline, PaymentInline]


@admin.register(WebhookLog)
class WebhookLogAdmin(admin.ModelAdmin):
    list_display = ['created_at', 'provider', 'event_type', 'resource_id', 'order', 'processed', 'error_message']
    list_filter = ['provider', 'event_type', 'processed', 'created_at']
    search_fields = ['resource_id', 'event_id', 'error_message']
    readonly_fields = ['provider', 'event_type', 'event_id', 'resource_id', 'order',
                       'payload', 'response_data', 'processed', 'error_message', 'created_at']
