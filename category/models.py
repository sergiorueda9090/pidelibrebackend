import uuid
import os
from django.db import models
from user.models import User


def category_image_path(instance, filename):
    ext = filename.split('.')[-1]
    unique_filename = f"{uuid.uuid4()}.{ext}"
    return os.path.join("categoria_image", unique_filename)


class Category(models.Model):
    user        = models.ForeignKey(User, on_delete=models.CASCADE, related_name='categories')
    name        = models.CharField(max_length=100)
    slug        = models.SlugField(max_length=120, unique=True)
    image       = models.ImageField(
                    upload_to=category_image_path,
                    null=True,
                    blank=True
                  )
    parent      = models.ForeignKey(
                    'self',
                    null=True,
                    blank=True,
                    on_delete=models.SET_NULL,
                    related_name='children'
                  )
    is_active   = models.BooleanField(default=True)
    order       = models.PositiveIntegerField(default=0)
    meta_title       = models.CharField(max_length=160, null=True, blank=True)
    meta_description = models.CharField(max_length=320, null=True, blank=True)
    updated_by  = models.ForeignKey(
                    User,
                    null=True,
                    blank=True,
                    on_delete=models.SET_NULL,
                    related_name='categories_updated'
                  )
    deleted_by  = models.ForeignKey(
                    User,
                    null=True,
                    blank=True,
                    on_delete=models.SET_NULL,
                    related_name='categories_deleted'
                  )
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)
    deleted_at  = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Categoría'
        verbose_name_plural = 'Categorías'
        db_table  = 'categories'
        ordering = ['order', 'name']

    def __str__(self):
        return self.name
