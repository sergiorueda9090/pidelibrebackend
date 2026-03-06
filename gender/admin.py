from django.contrib import admin
from .models import Gender


@admin.register(Gender)
class GenderAdmin(admin.ModelAdmin):
    list_display  = ('name', 'slug', 'created_at')
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}
