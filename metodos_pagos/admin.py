from django.contrib import admin
from .models import PaymentMethod


@admin.register(PaymentMethod)
class PaymentMethodAdmin(admin.ModelAdmin):
    list_display = ['name', 'provider', 'environment', 'is_active', 'order', 'currency', 'created_at']
    list_filter = ['provider', 'environment', 'is_active', 'created_at']
    search_fields = ['name', 'provider', 'description']
    readonly_fields = ['created_at', 'updated_at']
    list_editable = ['is_active', 'order']
