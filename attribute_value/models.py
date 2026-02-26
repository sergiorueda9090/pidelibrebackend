from django.db import models
from user.models import User
from attribute.models import Attribute


class AttributeValue(models.Model):
    user        = models.ForeignKey(User, on_delete=models.CASCADE, related_name='attribute_values')
    attribute   = models.ForeignKey(Attribute, on_delete=models.CASCADE, related_name='values')
    value       = models.CharField(max_length=100)
    color_hex   = models.CharField(max_length=7, null=True, blank=True)   # Solo para atributos de tipo color (#FF5733)
    order       = models.PositiveIntegerField(default=0)
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)
    deleted_at  = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name        = 'Valor de atributo'
        verbose_name_plural = 'Valores de atributo'
        db_table            = 'attribute_values'
        ordering            = ['attribute', 'order', 'value']
        unique_together     = [['attribute', 'value']]

    def __str__(self):
        return f'{self.attribute.name}: {self.value}'
