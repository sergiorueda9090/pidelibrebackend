from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import product.models


class Migration(migrations.Migration):

    dependencies = [
        ('attribute_value', '0001_initial'),
        ('product', '0002_productimage'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='ProductVariant',
            fields=[
                ('id',            models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sku',           models.CharField(max_length=100, unique=True)),
                ('price',         models.DecimalField(decimal_places=2, max_digits=10)),
                ('compare_price', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('stock',         models.PositiveIntegerField(default=0)),
                ('image',         models.ImageField(blank=True, null=True, upload_to=product.models.product_variant_image_path)),
                ('is_active',     models.BooleanField(default=True)),
                ('created_at',    models.DateTimeField(auto_now_add=True)),
                ('updated_at',    models.DateTimeField(auto_now=True)),
                ('deleted_at',    models.DateTimeField(blank=True, null=True)),
                ('user',          models.ForeignKey(
                                      on_delete=django.db.models.deletion.CASCADE,
                                      related_name='product_variants',
                                      to=settings.AUTH_USER_MODEL,
                                  )),
                ('product',       models.ForeignKey(
                                      on_delete=django.db.models.deletion.CASCADE,
                                      related_name='variants',
                                      to='product.product',
                                  )),
                ('attribute_values', models.ManyToManyField(
                                      blank=True,
                                      related_name='product_variants',
                                      to='attribute_value.attributevalue',
                                  )),
            ],
            options={
                'verbose_name':        'Variante de producto',
                'verbose_name_plural': 'Variantes de producto',
                'db_table':            'product_variants',
                'ordering':            ['product', 'created_at'],
            },
        ),
    ]
