import uuid
import os
from django.db import models
from user.models import User
from category.models import Category


def product_image_path(instance, filename):
    ext = filename.split('.')[-1]
    unique_filename = f"{uuid.uuid4()}.{ext}"
    return os.path.join("product_image", unique_filename)


def product_variant_image_path(instance, filename):
    ext = filename.split('.')[-1]
    unique_filename = f"{uuid.uuid4()}.{ext}"
    return os.path.join("product_variant_image", unique_filename)


class Product(models.Model):
    user         = models.ForeignKey(
                     User, on_delete=models.CASCADE,
                     related_name='products'
                   )
    updated_by   = models.ForeignKey(
                     User, null=True, blank=True,
                     on_delete=models.SET_NULL,
                     related_name='products_updated'
                   )
    deleted_by   = models.ForeignKey(
                     User, null=True, blank=True,
                     on_delete=models.SET_NULL,
                     related_name='products_deleted'
                   )
    category     = models.ForeignKey(
                     Category, null=True, blank=True,
                     on_delete=models.SET_NULL,
                     related_name='products'
                   )
    name              = models.CharField(max_length=200)
    slug              = models.SlugField(max_length=220, unique=True)
    description       = models.TextField(blank=True)
    short_description = models.TextField(blank=True)
    image        = models.ImageField(upload_to=product_image_path, null=True, blank=True)
    price        = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    compare_price     = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    cost_price        = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    sku          = models.CharField(max_length=100, null=True, blank=True, unique=True)
    stock        = models.PositiveIntegerField(null=True, blank=True)
    is_active    = models.BooleanField(default=True)
    is_featured  = models.BooleanField(default=False)
    is_new       = models.BooleanField(default=False)
    meta_title       = models.CharField(max_length=160, null=True, blank=True)
    meta_description = models.CharField(max_length=320, null=True, blank=True)
    created_at   = models.DateTimeField(auto_now_add=True)
    updated_at   = models.DateTimeField(auto_now=True)
    deleted_at   = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name        = 'Producto'
        verbose_name_plural = 'Productos'
        db_table            = 'products'
        ordering            = ['-created_at']

    def __str__(self):
        return self.name


class ProductImage(models.Model):
    product    = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image      = models.ImageField(upload_to=product_image_path)
    order      = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = 'Imagen de producto'
        verbose_name_plural = 'Imágenes de producto'
        db_table            = 'product_images'
        ordering            = ['order', 'created_at']

    def __str__(self):
        return f"{self.product.name} – img {self.order}"


class ProductVariant(models.Model):
    user             = models.ForeignKey(
                         User, on_delete=models.CASCADE,
                         related_name='product_variants'
                       )
    product          = models.ForeignKey(
                         Product, on_delete=models.CASCADE,
                         related_name='variants'
                       )
    attribute_values = models.ManyToManyField(
                         'attribute_value.AttributeValue',
                         related_name='product_variants',
                         blank=True,
                       )
    sku              = models.CharField(max_length=100, unique=True)
    price            = models.DecimalField(max_digits=10, decimal_places=2)
    compare_price    = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    stock            = models.PositiveIntegerField(default=0)
    image            = models.ImageField(upload_to=product_variant_image_path, null=True, blank=True)
    is_active        = models.BooleanField(default=True)
    created_at       = models.DateTimeField(auto_now_add=True)
    updated_at       = models.DateTimeField(auto_now=True)
    deleted_at       = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name        = 'Variante de producto'
        verbose_name_plural = 'Variantes de producto'
        db_table            = 'product_variants'
        ordering            = ['product', 'created_at']

    def __str__(self):
        return f"{self.product.name} – {self.sku}"
