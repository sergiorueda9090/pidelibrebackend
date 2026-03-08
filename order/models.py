import uuid
from django.db import models
from customer.models import Customer
from product.models import Product, ProductVariant


class Order(models.Model):
    class Status(models.TextChoices):
        PENDING_PAYMENT = 'pending_payment', 'Pendiente de pago'
        APPROVED        = 'approved',        'Aprobado'
        REJECTED        = 'rejected',        'Rechazado'
        CANCELLED       = 'cancelled',       'Cancelado'
        SHIPPED         = 'shipped',         'Enviado'
        DELIVERED       = 'delivered',       'Entregado'

    order_number    = models.CharField(max_length=30, unique=True, editable=False)
    customer        = models.ForeignKey(
                        Customer, on_delete=models.SET_NULL,
                        null=True, blank=True, related_name='orders'
                      )
    # Snapshot de datos del comprador
    email           = models.EmailField()
    first_name      = models.CharField(max_length=100)
    last_name       = models.CharField(max_length=100)
    phone           = models.CharField(max_length=20)
    document_number = models.CharField(max_length=30, blank=True, default='')
    # Dirección de envío
    address         = models.CharField(max_length=255)
    address2        = models.CharField(max_length=255, blank=True, default='')
    city            = models.CharField(max_length=100)
    state           = models.CharField(max_length=100, blank=True, default='')
    country         = models.CharField(max_length=100, default='Colombia')
    postal_code     = models.CharField(max_length=20, blank=True, default='')
    notes           = models.TextField(blank=True, default='')
    # Estado y pago
    status          = models.CharField(
                        max_length=20,
                        choices=Status.choices,
                        default=Status.PENDING_PAYMENT,
                      )
    payment_method  = models.CharField(max_length=20)
    # Totales
    subtotal        = models.DecimalField(max_digits=12, decimal_places=2)
    shipping_cost   = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total           = models.DecimalField(max_digits=12, decimal_places=2)
    # Timestamps
    created_at      = models.DateTimeField(auto_now_add=True)
    updated_at      = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Orden'
        verbose_name_plural = 'Órdenes'
        db_table = 'orders'
        ordering = ['-created_at']

    def __str__(self):
        return self.order_number

    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = self._generate_order_number()
        super().save(*args, **kwargs)

    @staticmethod
    def _generate_order_number():
        from django.utils import timezone
        date_str = timezone.now().strftime('%Y%m%d')
        short_uuid = uuid.uuid4().hex[:6].upper()
        return f'PL-{date_str}-{short_uuid}'


class OrderItem(models.Model):
    order           = models.ForeignKey(
                        Order, on_delete=models.CASCADE,
                        related_name='items'
                      )
    product         = models.ForeignKey(
                        Product, on_delete=models.SET_NULL,
                        null=True, blank=True, related_name='order_items'
                      )
    variant         = models.ForeignKey(
                        ProductVariant, on_delete=models.SET_NULL,
                        null=True, blank=True, related_name='order_items'
                      )
    # Snapshots al momento de la compra
    product_name    = models.CharField(max_length=200)
    product_image   = models.URLField(max_length=500, blank=True, default='')
    sku             = models.CharField(max_length=100, blank=True, default='')
    attributes      = models.JSONField(default=dict, blank=True)
    price           = models.DecimalField(max_digits=10, decimal_places=2)
    quantity        = models.PositiveIntegerField()
    total           = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        verbose_name = 'Ítem de orden'
        verbose_name_plural = 'Ítems de orden'
        db_table = 'order_items'

    def __str__(self):
        return f"{self.product_name} x{self.quantity}"

    def save(self, *args, **kwargs):
        self.total = self.price * self.quantity
        super().save(*args, **kwargs)


class Payment(models.Model):
    class Status(models.TextChoices):
        PENDING  = 'pending',  'Pendiente'
        APPROVED = 'approved', 'Aprobado'
        REJECTED = 'rejected', 'Rechazado'
        REFUNDED = 'refunded', 'Reembolsado'

    order           = models.ForeignKey(
                        Order, on_delete=models.CASCADE,
                        related_name='payments'
                      )
    provider        = models.CharField(max_length=20)
    transaction_id  = models.CharField(max_length=255, blank=True, default='')
    status          = models.CharField(
                        max_length=20,
                        choices=Status.choices,
                        default=Status.PENDING,
                      )
    amount          = models.DecimalField(max_digits=12, decimal_places=2)
    raw_response    = models.JSONField(default=dict, blank=True)
    created_at      = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Pago'
        verbose_name_plural = 'Pagos'
        db_table = 'payments'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.provider} – {self.transaction_id} – {self.status}"


class WebhookLog(models.Model):
    """Registro de cada webhook recibido de pasarelas de pago."""
    provider        = models.CharField(max_length=30)
    event_type      = models.CharField(max_length=50)
    event_id        = models.CharField(max_length=100, blank=True, default='')
    resource_id     = models.CharField(max_length=100, blank=True, default='')
    order           = models.ForeignKey(
                        Order, on_delete=models.SET_NULL,
                        null=True, blank=True, related_name='webhook_logs'
                      )
    status_code     = models.IntegerField(default=200)
    payload         = models.JSONField(default=dict)
    response_data   = models.JSONField(default=dict)
    processed       = models.BooleanField(default=False)
    error_message   = models.TextField(blank=True, default='')
    created_at      = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Webhook Log'
        verbose_name_plural = 'Webhook Logs'
        db_table = 'webhook_logs'
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.provider}] {self.event_type} — {self.created_at:%Y-%m-%d %H:%M}"
