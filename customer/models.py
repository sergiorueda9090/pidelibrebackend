from django.conf import settings
from django.db import models
from gender.models import Gender


class Customer(models.Model):
    user            = models.OneToOneField(
                        settings.AUTH_USER_MODEL,
                        on_delete=models.CASCADE,
                        related_name='customer',
                        null=True, blank=True,
                      )
    first_name      = models.CharField(max_length=100)
    last_name       = models.CharField(max_length=100)
    email           = models.EmailField(unique=True)
    phone           = models.CharField(max_length=20, null=True, blank=True)
    document_number = models.CharField(max_length=30, null=True, blank=True)
    date_of_birth   = models.DateField(null=True, blank=True)
    gender          = models.ForeignKey(
                        Gender, null=True, blank=True,
                        on_delete=models.SET_NULL,
                        related_name='customers'
                      )
    is_active       = models.BooleanField(default=True)
    created_at      = models.DateTimeField(auto_now_add=True)
    updated_at      = models.DateTimeField(auto_now=True)
    deleted_at      = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Cliente'
        verbose_name_plural = 'Clientes'
        db_table = 'customers'
        ordering = ['first_name', 'last_name']

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"


class CustomerAddress(models.Model):
    customer    = models.ForeignKey(
                    Customer, on_delete=models.CASCADE,
                    related_name='addresses'
                  )
    address     = models.CharField(max_length=255)
    city        = models.CharField(max_length=100)
    state       = models.CharField(max_length=100, null=True, blank=True)
    country     = models.CharField(max_length=100, default='Colombia')
    postal_code = models.CharField(max_length=20, null=True, blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Dirección de cliente'
        verbose_name_plural = 'Direcciones de clientes'
        db_table = 'customer_addresses'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.address}, {self.city} – {self.customer}"
