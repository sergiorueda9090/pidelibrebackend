from django.db import migrations, models
import django.db.models.deletion
import product.models


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ProductImage',
            fields=[
                ('id',         models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image',      models.ImageField(upload_to=product.models.product_image_path)),
                ('order',      models.PositiveIntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('product',    models.ForeignKey(
                                    on_delete=django.db.models.deletion.CASCADE,
                                    related_name='images',
                                    to='product.product',
                               )),
            ],
            options={
                'verbose_name':        'Imagen de producto',
                'verbose_name_plural': 'Imágenes de producto',
                'db_table':            'product_images',
                'ordering':            ['order', 'created_at'],
            },
        ),
    ]
