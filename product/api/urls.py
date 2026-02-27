from django.urls import path
from . import views

urlpatterns = [
    # ── Producto ──────────────────────────────────────────────────────────────
    path('create/',                          views.create_data,       name='product_create'),
    path('all/',                             views.get_all_data,      name='product_all'),
    path('<int:id>/',                        views.get_by_id,         name='product_by_id'),
    path('<int:id>/update/',                 views.update_data,       name='product_update'),
    path('<int:id>/delete/',                 views.delete_data,       name='product_delete'),
    # ── Galería de imágenes ───────────────────────────────────────────────────
    path('<int:id>/images/upload/',          views.upload_images,     name='product_images_upload'),
    path('<int:id>/images/reorder/',         views.reorder_images,    name='product_images_reorder'),
    path('images/<int:image_id>/delete/',    views.delete_image,      name='product_image_delete'),
    # ── Variantes ─────────────────────────────────────────────────────────────
    path('<int:id>/variants/',               views.get_variants,      name='product_variants'),
    path('<int:id>/variants/create/',        views.create_variant,    name='product_variant_create'),
    path('variants/<int:variant_id>/',       views.get_variant_by_id, name='product_variant_by_id'),
    path('variants/<int:variant_id>/update/', views.update_variant,   name='product_variant_update'),
    path('variants/<int:variant_id>/delete/', views.delete_variant,   name='product_variant_delete'),
]
