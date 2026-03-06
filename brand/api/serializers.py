from rest_framework import serializers
from brand.models import Brand


class BrandSerializer(serializers.ModelSerializer):
    logo = serializers.ImageField(required=False, allow_null=True)

    class Meta:
        model  = Brand
        fields = [
            'name', 'slug', 'logo', 'description', 'is_active',
        ]

    def validate_slug(self, value):
        if Brand.objects.filter(slug=value).exists():
            raise serializers.ValidationError("This slug already exists.")
        return value

    def create(self, validated_data):
        logo = validated_data.pop('logo', None)
        brand = Brand.objects.create(**validated_data)
        if logo:
            brand.logo = logo
            brand.save()
        return brand


class BrandListSerializer(serializers.ModelSerializer):
    logo = serializers.SerializerMethodField()

    class Meta:
        model  = Brand
        fields = [
            'id', 'name', 'slug', 'logo',
            'is_active', 'deleted_at', 'created_at',
        ]

    def get_logo(self, obj):
        if obj.logo:
            return obj.logo.url
        return None


class BrandDetailSerializer(serializers.ModelSerializer):
    logo       = serializers.SerializerMethodField()
    user       = serializers.SerializerMethodField()
    updated_by = serializers.SerializerMethodField()
    deleted_by = serializers.SerializerMethodField()

    class Meta:
        model  = Brand
        fields = [
            'id', 'user', 'name', 'slug', 'logo', 'description',
            'is_active',
            'updated_by', 'deleted_by',
            'created_at', 'updated_at', 'deleted_at',
        ]

    def get_logo(self, obj):
        if obj.logo:
            return obj.logo.url
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


class BrandUpdateSerializer(serializers.ModelSerializer):
    logo = serializers.ImageField(required=False, allow_null=True)

    class Meta:
        model  = Brand
        fields = [
            'name', 'slug', 'logo', 'description', 'is_active',
        ]

    def validate_slug(self, value):
        qs = Brand.objects.filter(slug=value).exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("This slug already exists.")
        return value

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance
