import uuid
import os
from django.db import models
from user.models import User


def brand_logo_path(instance, filename):
    ext = filename.split('.')[-1]
    unique_filename = f"{uuid.uuid4()}.{ext}"
    return os.path.join("brand_logo", unique_filename)


class Brand(models.Model):
    user        = models.ForeignKey(User, on_delete=models.CASCADE, related_name='brands')
    name        = models.CharField(max_length=100)
    slug        = models.SlugField(max_length=120, unique=True)
    logo        = models.ImageField(
                    upload_to=brand_logo_path,
                    null=True,
                    blank=True
                  )
    description = models.TextField(null=True, blank=True)
    is_active   = models.BooleanField(default=True)
    updated_by  = models.ForeignKey(
                    User,
                    null=True,
                    blank=True,
                    on_delete=models.SET_NULL,
                    related_name='brands_updated'
                  )
    deleted_by  = models.ForeignKey(
                    User,
                    null=True,
                    blank=True,
                    on_delete=models.SET_NULL,
                    related_name='brands_deleted'
                  )
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)
    deleted_at  = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Marca'
        verbose_name_plural = 'Marcas'
        db_table = 'brands'
        ordering = ['name']

    def __str__(self):
        return self.name
