from rest_framework import serializers
from category.models import Category
from brand.models    import Brand
from gender.models   import Gender
from product.models  import Product, ProductImage, ProductVariant
from attribute_value.models import AttributeValue


# ── Imágenes de galería ────────────────────────────────────────────────────────
class ProductImageSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()

    class Meta:
        model  = ProductImage
        fields = ['id', 'url', 'order', 'created_at']

    def get_url(self, obj):
        request = self.context.get('request')
        if obj.image:
            return request.build_absolute_uri(obj.image.url) if request else obj.image.url
        return None


# ── Helper: limpia el HTML vacío que envía Quill ──────────────────────────────
_QUILL_EMPTY = {'<p><br></p>', '<p></p>', '<br>'}

def _clean_html(value):
    """Devuelve '' si Quill envió un editor vacío; de lo contrario devuelve el HTML tal cual."""
    if not value:
        return ''
    return '' if value.strip() in _QUILL_EMPTY else value.strip()


# ── Creación ──────────────────────────────────────────────────────────────────
class ProductSerializer(serializers.ModelSerializer):
    """Usado en creación."""
    category          = serializers.PrimaryKeyRelatedField(queryset=Category.objects.all(), required=False, allow_null=True)
    brand             = serializers.PrimaryKeyRelatedField(queryset=Brand.objects.all(), required=False, allow_null=True)
    gender            = serializers.PrimaryKeyRelatedField(queryset=Gender.objects.all(), required=False, allow_null=True)
    image             = serializers.ImageField(required=False, allow_null=True)
    description       = serializers.CharField(required=False, allow_blank=True, default='')
    short_description = serializers.CharField(required=False, allow_blank=True, default='')
    price             = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, allow_null=True)
    compare_price     = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, allow_null=True)
    cost_price        = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, allow_null=True)
    sku               = serializers.CharField(max_length=100, required=False, allow_null=True, allow_blank=True)
    stock             = serializers.IntegerField(required=False, allow_null=True, min_value=0)

    class Meta:
        model  = Product
        fields = [
            'category', 'brand', 'gender',
            'name', 'slug', 'description', 'short_description',
            'image', 'price', 'compare_price', 'cost_price',
            'sku', 'stock', 'is_active', 'is_featured', 'is_new',
            'meta_title', 'meta_description',
        ]

    def validate_description(self, value):
        return _clean_html(value)

    def validate_short_description(self, value):
        return _clean_html(value)

    def validate_slug(self, value):
        if Product.objects.filter(slug=value).exists():
            raise serializers.ValidationError("A product with this slug already exists.")
        return value

    def validate_sku(self, value):
        if value and Product.objects.filter(sku=value).exists():
            raise serializers.ValidationError("A product with this SKU already exists.")
        return value

    def validate(self, data):
        price         = data.get('price')
        compare_price = data.get('compare_price')
        if price is not None and compare_price is not None:
            if compare_price <= price:
                raise serializers.ValidationError(
                    {'compare_price': 'compare_price must be greater than price.'}
                )
        return data


# ── Listado paginado ───────────────────────────────────────────────────────────
class ProductListSerializer(serializers.ModelSerializer):
    """Usado en el listado paginado."""
    category = serializers.SerializerMethodField()
    brand    = serializers.SerializerMethodField()
    gender   = serializers.SerializerMethodField()
    image    = serializers.SerializerMethodField()

    class Meta:
        model  = Product
        fields = [
            'id', 'category', 'brand', 'gender',
            'name', 'slug', 'short_description',
            'image', 'price', 'compare_price', 'sku', 'stock',
            'is_active', 'is_featured', 'is_new',
            'created_at', 'deleted_at',
        ]

    def get_category(self, obj):
        if obj.category:
            return {'id': obj.category.id, 'name': obj.category.name}
        return None

    def get_brand(self, obj):
        if obj.brand:
            return {'id': obj.brand.id, 'name': obj.brand.name}
        return None

    def get_gender(self, obj):
        if obj.gender:
            return {'id': obj.gender.id, 'name': obj.gender.name}
        return None

    def get_image(self, obj):
        if obj.image:
            request = self.context.get('request')
            return request.build_absolute_uri(obj.image.url) if request else obj.image.url
        return None


# ── Detalle completo ───────────────────────────────────────────────────────────
class ProductDetailSerializer(serializers.ModelSerializer):
    """Usado en create/get-by-id para devolver el registro completo."""
    category   = serializers.SerializerMethodField()
    brand      = serializers.SerializerMethodField()
    gender     = serializers.SerializerMethodField()
    user       = serializers.SerializerMethodField()
    updated_by = serializers.SerializerMethodField()
    deleted_by = serializers.SerializerMethodField()
    image      = serializers.SerializerMethodField()
    images     = serializers.SerializerMethodField()
    variants   = serializers.SerializerMethodField()

    class Meta:
        model  = Product
        fields = [
            'id', 'user', 'updated_by', 'deleted_by',
            'category', 'brand', 'gender',
            'name', 'slug', 'description', 'short_description',
            'image', 'images', 'variants',
            'price', 'compare_price', 'cost_price',
            'sku', 'stock', 'is_active', 'is_featured', 'is_new',
            'meta_title', 'meta_description',
            'created_at', 'updated_at', 'deleted_at',
        ]

    def get_category(self, obj):
        if obj.category:
            return {'id': obj.category.id, 'name': obj.category.name}
        return None

    def get_brand(self, obj):
        if obj.brand:
            return {'id': obj.brand.id, 'name': obj.brand.name}
        return None

    def get_gender(self, obj):
        if obj.gender:
            return {'id': obj.gender.id, 'name': obj.gender.name}
        return None

    def get_user(self, obj):
        return {'id': obj.user.id, 'username': obj.user.username}

    def get_updated_by(self, obj):
        if obj.updated_by:
            return {'id': obj.updated_by.id, 'username': obj.updated_by.username}
        return None

    def get_deleted_by(self, obj):
        if obj.deleted_by:
            return {'id': obj.deleted_by.id, 'username': obj.deleted_by.username}
        return None

    def get_image(self, obj):
        if obj.image:
            request = self.context.get('request')
            return request.build_absolute_uri(obj.image.url) if request else obj.image.url
        return None

    def get_images(self, obj):
        request = self.context.get('request')
        return ProductImageSerializer(obj.images.all(), many=True, context={'request': request}).data

    def get_variants(self, obj):
        request = self.context.get('request')
        qs = obj.variants.filter(deleted_at__isnull=True)
        return ProductVariantListSerializer(qs, many=True, context={'request': request}).data


# ── Actualización parcial ──────────────────────────────────────────────────────
class ProductUpdateSerializer(serializers.ModelSerializer):
    """Usado en actualización parcial."""
    category          = serializers.PrimaryKeyRelatedField(queryset=Category.objects.all(), required=False, allow_null=True)
    brand             = serializers.PrimaryKeyRelatedField(queryset=Brand.objects.all(), required=False, allow_null=True)
    gender            = serializers.PrimaryKeyRelatedField(queryset=Gender.objects.all(), required=False, allow_null=True)
    image             = serializers.ImageField(required=False, allow_null=True)
    description       = serializers.CharField(required=False, allow_blank=True)
    short_description = serializers.CharField(required=False, allow_blank=True)
    price             = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, allow_null=True)
    compare_price     = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, allow_null=True)
    cost_price        = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, allow_null=True)
    sku               = serializers.CharField(max_length=100, required=False, allow_null=True, allow_blank=True)
    stock             = serializers.IntegerField(required=False, allow_null=True, min_value=0)

    class Meta:
        model  = Product
        fields = [
            'category', 'brand', 'gender',
            'name', 'slug', 'description', 'short_description',
            'image', 'price', 'compare_price', 'cost_price',
            'sku', 'stock', 'is_active', 'is_featured', 'is_new',
            'meta_title', 'meta_description',
        ]

    def validate_description(self, value):
        return _clean_html(value)

    def validate_short_description(self, value):
        return _clean_html(value)

    def validate_slug(self, value):
        qs = Product.objects.filter(slug=value).exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("A product with this slug already exists.")
        return value

    def validate_sku(self, value):
        if value:
            qs = Product.objects.filter(sku=value).exclude(pk=self.instance.pk)
            if qs.exists():
                raise serializers.ValidationError("A product with this SKU already exists.")
        return value

    def validate(self, data):
        price         = data.get('price', self.instance.price)
        compare_price = data.get('compare_price', self.instance.compare_price)
        if price is not None and compare_price is not None:
            if compare_price <= price:
                raise serializers.ValidationError(
                    {'compare_price': 'compare_price must be greater than price.'}
                )
        return data

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


# ── Variantes ──────────────────────────────────────────────────────────────────

class ProductVariantListSerializer(serializers.ModelSerializer):
    """Usado en el listado de variantes de un producto."""
    attribute_values = serializers.SerializerMethodField()
    image            = serializers.SerializerMethodField()

    class Meta:
        model  = ProductVariant
        fields = [
            'id', 'sku', 'price', 'compare_price', 'stock',
            'image', 'is_active', 'attribute_values',
            'created_at', 'deleted_at',
        ]

    def get_attribute_values(self, obj):
        return [
            {
                'id':        av.id,
                'value':     av.value,
                'color_hex': av.color_hex,
                'attribute': {'id': av.attribute.id, 'name': av.attribute.name},
            }
            for av in obj.attribute_values.select_related('attribute').all()
        ]

    def get_image(self, obj):
        if obj.image:
            request = self.context.get('request')
            return request.build_absolute_uri(obj.image.url) if request else obj.image.url
        return None


class ProductVariantDetailSerializer(serializers.ModelSerializer):
    """Usado en get-by-id de una variante."""
    attribute_values = serializers.SerializerMethodField()
    image            = serializers.SerializerMethodField()
    user             = serializers.SerializerMethodField()
    product          = serializers.SerializerMethodField()

    class Meta:
        model  = ProductVariant
        fields = [
            'id', 'user', 'product',
            'sku', 'price', 'compare_price', 'stock',
            'image', 'is_active', 'attribute_values',
            'created_at', 'updated_at', 'deleted_at',
        ]

    def get_attribute_values(self, obj):
        return [
            {
                'id':        av.id,
                'value':     av.value,
                'color_hex': av.color_hex,
                'attribute': {'id': av.attribute.id, 'name': av.attribute.name},
            }
            for av in obj.attribute_values.select_related('attribute').all()
        ]

    def get_image(self, obj):
        if obj.image:
            request = self.context.get('request')
            return request.build_absolute_uri(obj.image.url) if request else obj.image.url
        return None

    def get_user(self, obj):
        return {'id': obj.user.id, 'username': obj.user.username}

    def get_product(self, obj):
        return {'id': obj.product.id, 'name': obj.product.name, 'slug': obj.product.slug}


class ProductVariantSerializer(serializers.ModelSerializer):
    """Usado en creación de variante."""
    attribute_values = serializers.PrimaryKeyRelatedField(
        queryset=AttributeValue.objects.all(), many=True, required=False
    )
    image         = serializers.ImageField(required=False, allow_null=True)
    compare_price = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, allow_null=True)

    class Meta:
        model  = ProductVariant
        fields = [
            'sku', 'price', 'compare_price', 'stock',
            'image', 'is_active', 'attribute_values',
        ]

    def validate_sku(self, value):
        if ProductVariant.objects.filter(sku=value).exists():
            raise serializers.ValidationError("Ya existe una variante con este SKU.")
        return value

    def validate(self, data):
        price         = data.get('price')
        compare_price = data.get('compare_price')
        if price is not None and compare_price is not None:
            if compare_price <= price:
                raise serializers.ValidationError(
                    {'compare_price': 'compare_price debe ser mayor que price.'}
                )
        return data

    def create(self, validated_data):
        attribute_values = validated_data.pop('attribute_values', [])
        variant = ProductVariant.objects.create(**validated_data)
        if attribute_values:
            variant.attribute_values.set(attribute_values)
        return variant


class ProductVariantUpdateSerializer(serializers.ModelSerializer):
    """Usado en actualización parcial de variante."""
    attribute_values = serializers.PrimaryKeyRelatedField(
        queryset=AttributeValue.objects.all(), many=True, required=False
    )
    image         = serializers.ImageField(required=False, allow_null=True)
    compare_price = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, allow_null=True)
    price         = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    stock         = serializers.IntegerField(required=False, min_value=0)

    class Meta:
        model  = ProductVariant
        fields = [
            'sku', 'price', 'compare_price', 'stock',
            'image', 'is_active', 'attribute_values',
        ]

    def validate_sku(self, value):
        qs = ProductVariant.objects.filter(sku=value).exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("Ya existe una variante con este SKU.")
        return value

    def validate(self, data):
        price         = data.get('price', self.instance.price)
        compare_price = data.get('compare_price', self.instance.compare_price)
        if price is not None and compare_price is not None:
            if compare_price <= price:
                raise serializers.ValidationError(
                    {'compare_price': 'compare_price debe ser mayor que price.'}
                )
        return data

    def update(self, instance, validated_data):
        attribute_values = validated_data.pop('attribute_values', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if attribute_values is not None:
            instance.attribute_values.set(attribute_values)
        return instance
