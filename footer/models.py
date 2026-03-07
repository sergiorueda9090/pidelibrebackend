import uuid
import os
from django.db import models
from django.conf import settings


def footer_logo_path(instance, filename):
    ext = filename.split('.')[-1]
    unique_filename = f"{uuid.uuid4()}.{ext}"
    return os.path.join("footer_image", unique_filename)


def footer_payment_path(instance, filename):
    ext = filename.split('.')[-1]
    unique_filename = f"{uuid.uuid4()}.{ext}"
    return os.path.join("footer_image", unique_filename)


class Footer(models.Model):
    user            = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    logo            = models.FileField(upload_to=footer_logo_path, null=True, blank=True)
    description     = models.CharField(max_length=200, blank=True)
    facebook_url    = models.URLField(max_length=500, blank=True)
    twitter_url     = models.URLField(max_length=500, blank=True)
    linkedin_url    = models.URLField(max_length=500, blank=True)
    instagram_url   = models.URLField(max_length=500, blank=True)
    phone           = models.CharField(max_length=30, blank=True)
    phone_label     = models.CharField(max_length=100, blank=True)
    email           = models.EmailField(blank=True)
    copyright_text  = models.CharField(max_length=200, blank=True)
    payment_image   = models.FileField(upload_to=footer_payment_path, null=True, blank=True)
    is_active       = models.BooleanField(default=True)
    created_at      = models.DateTimeField(auto_now_add=True)
    updated_at      = models.DateTimeField(auto_now=True)
    deleted_at      = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Footer'
        verbose_name_plural = 'Footers'
        db_table = 'footers'

    def __str__(self):
        return f"Footer #{self.id}"
