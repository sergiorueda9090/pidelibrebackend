import uuid
import os
from django.db import models
from user.models import User
from product.models import Product


def slider_image_path(instance, filename):
    ext = filename.split('.')[-1]
    unique_filename = f"{uuid.uuid4()}.{ext}"
    return os.path.join("slider_image", unique_filename)


class Slider(models.Model):
    # --- Contenido ---
    user = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='sliders'
    )
    updated_by = models.ForeignKey(
        User, null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='sliders_updated'
    )
    deleted_by = models.ForeignKey(
        User, null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='sliders_deleted'
    )
    title = models.CharField(max_length=200)
    subtitle = models.CharField(max_length=100, blank=True)
    discount_percentage = models.IntegerField(null=True, blank=True)
    offer_text = models.CharField(max_length=100, default="off this week")
    button_text = models.CharField(max_length=50, default="Shop Now")

    # --- Vinculacion flexible ---
    product = models.ForeignKey(
        Product,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sliders',
        help_text="Si se selecciona, el boton lleva al producto y puede usar su imagen"
    )
    custom_url = models.CharField(max_length=500, blank=True, help_text="URL manual si no hay producto")
    custom_image = models.ImageField(
        upload_to=slider_image_path,
        null=True,
        blank=True,
        help_text="Imagen manual si no hay producto"
    )

    # --- Apariencia ---
    bg_color = models.CharField(max_length=7, default="#0989FF")
    is_light = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Slider'
        verbose_name_plural = 'Sliders'
        db_table = 'sliders'
        ordering = ['order']

    @property
    def image(self):
        """Prioridad: imagen custom > imagen del producto"""
        if self.custom_image:
            return self.custom_image.url
        if self.product and self.product.image:
            return self.product.image.url
        return None

    @property
    def url(self):
        """Prioridad: producto > URL custom"""
        if self.product:
            return f"/producto/{self.product.id}"
        return self.custom_url or "/shop"

    @property
    def price(self):
        """Si hay producto, usa su precio real"""
        if self.product:
            return self.product.price
        return None

    def __str__(self):
        return self.title
