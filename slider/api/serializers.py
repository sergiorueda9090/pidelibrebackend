from rest_framework import serializers
from slider.models import Slider


class SliderSerializer(serializers.ModelSerializer):
    custom_image = serializers.ImageField(required=False, allow_null=True)
    product = serializers.PrimaryKeyRelatedField(
        queryset=Slider._meta.get_field('product').related_model.objects.all(),
        required=False,
        allow_null=True
    )

    class Meta:
        model = Slider
        fields = [
            'title', 'subtitle', 'discount_percentage', 'offer_text',
            'button_text', 'product', 'custom_url', 'custom_image',
            'bg_color', 'is_light', 'order', 'is_active',
        ]

    def create(self, validated_data):
        custom_image = validated_data.pop('custom_image', None)
        slider = Slider.objects.create(**validated_data)
        if custom_image:
            slider.custom_image = custom_image
            slider.save()
        return slider


class SliderListSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()
    url = serializers.SerializerMethodField()
    price = serializers.SerializerMethodField()
    product = serializers.SerializerMethodField()

    class Meta:
        model = Slider
        fields = [
            'id', 'title', 'subtitle', 'discount_percentage', 'offer_text',
            'button_text', 'product', 'image', 'url', 'price',
            'bg_color', 'is_light', 'order', 'is_active',
            'deleted_at', 'created_at',
        ]

    def get_image(self, obj):
        return obj.image

    def get_url(self, obj):
        return obj.url

    def get_price(self, obj):
        return str(obj.price) if obj.price else None

    def get_product(self, obj):
        if obj.product:
            return {'id': obj.product.id, 'name': obj.product.name}
        return None


class SliderDetailSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()
    url = serializers.SerializerMethodField()
    price = serializers.SerializerMethodField()
    custom_image = serializers.SerializerMethodField()
    product = serializers.SerializerMethodField()
    user = serializers.SerializerMethodField()
    updated_by = serializers.SerializerMethodField()
    deleted_by = serializers.SerializerMethodField()

    class Meta:
        model = Slider
        fields = [
            'id', 'user', 'title', 'subtitle', 'discount_percentage', 'offer_text',
            'button_text', 'product', 'custom_url', 'custom_image',
            'image', 'url', 'price',
            'bg_color', 'is_light', 'order', 'is_active',
            'updated_by', 'deleted_by',
            'created_at', 'updated_at', 'deleted_at',
        ]

    def get_image(self, obj):
        return obj.image

    def get_url(self, obj):
        return obj.url

    def get_price(self, obj):
        return str(obj.price) if obj.price else None

    def get_custom_image(self, obj):
        if obj.custom_image:
            return obj.custom_image.url
        return None

    def get_product(self, obj):
        if obj.product:
            return {
                'id': obj.product.id,
                'name': obj.product.name,
                'price': str(obj.product.price) if obj.product.price else None,
                'image': obj.product.image.url if obj.product.image else None,
            }
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


class SliderUpdateSerializer(serializers.ModelSerializer):
    custom_image = serializers.ImageField(required=False, allow_null=True)

    class Meta:
        model = Slider
        fields = [
            'title', 'subtitle', 'discount_percentage', 'offer_text',
            'button_text', 'product', 'custom_url', 'custom_image',
            'bg_color', 'is_light', 'order', 'is_active',
        ]

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance
