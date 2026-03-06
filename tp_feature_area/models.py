from django.db import models
from django.conf import settings


class TpFeatureArea(models.Model):
    user        = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    icon        = models.TextField(help_text="Codigo SVG del icono")
    title       = models.CharField(max_length=100)
    description = models.CharField(max_length=200)
    order       = models.PositiveIntegerField(default=0)
    is_active   = models.BooleanField(default=True)
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)
    deleted_at  = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.title
