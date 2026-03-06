from django.contrib import admin
from .models import Customer, CustomerAddress


class CustomerAddressInline(admin.TabularInline):
    model = CustomerAddress
    extra = 0


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display  = ('first_name', 'last_name', 'email', 'phone', 'is_active', 'created_at')
    list_filter   = ('is_active', 'gender')
    search_fields = ('first_name', 'last_name', 'email', 'document_number')
    inlines       = [CustomerAddressInline]


@admin.register(CustomerAddress)
class CustomerAddressAdmin(admin.ModelAdmin):
    list_display  = ('customer', 'address', 'city', 'state', 'country')
    search_fields = ('address', 'city', 'customer__first_name', 'customer__last_name')
