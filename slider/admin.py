from django.contrib import admin
from .models import Slider


@admin.register(Slider)
class SliderAdmin(admin.ModelAdmin):
    list_display = ('title', 'order', 'is_active', 'product', 'created_at')
    list_filter = ('is_active', 'is_light')
    search_fields = ('title', 'subtitle')
    ordering = ('order',)
