import uuid
import os
from django.db import models
from django.conf import settings


def payment_method_logo_path(instance, filename):
    ext = filename.split('.')[-1]
    unique_filename = f"{uuid.uuid4()}.{ext}"
    return os.path.join("payment_method_image", unique_filename)


class PaymentMethod(models.Model):
    class Provider(models.TextChoices):
        MERCADOPAGO = 'mercadopago', 'Mercado Pago'
        WOMPI       = 'wompi',       'Wompi'
        PAYPAL      = 'paypal',      'PayPal'
        STRIPE      = 'stripe',      'Stripe'
        OTHER       = 'other',       'Otro'

    class Environment(models.TextChoices):
        SANDBOX    = 'sandbox',    'Sandbox / Pruebas'
        PRODUCTION = 'production', 'Produccion'

    # Relacion
    user                = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    # Identificacion
    provider            = models.CharField(max_length=20, choices=Provider.choices)
    name                = models.CharField(max_length=100)
    description         = models.TextField(blank=True, default='')
    logo                = models.FileField(upload_to=payment_method_logo_path, null=True, blank=True)

    # Credenciales
    public_key          = models.CharField(max_length=255, blank=True, default='')
    access_token        = models.CharField(max_length=255)
    secret_key          = models.CharField(max_length=255, blank=True, default='')
    client_id           = models.CharField(max_length=255, blank=True, default='')
    webhook_secret      = models.CharField(max_length=255, blank=True, default='')
    extra_config        = models.JSONField(default=dict, blank=True)

    # Entorno
    environment         = models.CharField(max_length=20, choices=Environment.choices, default=Environment.SANDBOX)

    # Estado y orden
    is_active           = models.BooleanField(default=True)
    order               = models.PositiveIntegerField(default=0)

    # Configuracion de pago
    currency            = models.CharField(max_length=10, default='COP')
    supported_countries = models.JSONField(default=list, blank=True)

    # Auditoria
    created_at          = models.DateTimeField(auto_now_add=True)
    updated_at          = models.DateTimeField(auto_now=True)
    deleted_at          = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Metodo de Pago'
        verbose_name_plural = 'Metodos de Pago'
        db_table = 'payment_methods'
        ordering = ['order', 'name']
        unique_together = [['provider', 'environment']]

    def __str__(self):
        return f"{self.name} ({self.get_environment_display()})"
