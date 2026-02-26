from django.db import models
from user.models import User

class Attribute(models.Model):
    user        = models.ForeignKey(User, on_delete=models.CASCADE, related_name='attributes')
    name        = models.CharField(max_length=100, unique=True)
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)
    deleted_at  = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name        = 'Atributo'
        verbose_name_plural = 'Atributos'
        db_table            = 'attributes'
        ordering            = ['name']

    def __str__(self):
        return self.name
