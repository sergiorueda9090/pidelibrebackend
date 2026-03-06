from django.db import models
from user.models import User


class Gender(models.Model):
    user        = models.ForeignKey(User, on_delete=models.CASCADE, related_name='genders')
    name        = models.CharField(max_length=100)
    slug        = models.SlugField(max_length=120, unique=True)
    description = models.TextField(null=True, blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)
    deleted_at  = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Genero'
        verbose_name_plural = 'Generos'
        db_table = 'genders'
        ordering = ['name']

    def __str__(self):
        return self.name
