from rest_framework import serializers
from category.models import Category


class CategorySerializer(serializers.ModelSerializer):
    image  = serializers.ImageField(required=False, allow_null=True)
    parent = serializers.PrimaryKeyRelatedField(
                queryset=Category.objects.all(),
                required=False,
                allow_null=True
             )

    class Meta:
        model  = Category
        fields = [
            'name', 'slug', 'image', 'parent',
            'is_active', 'order', 'meta_title', 'meta_description',
        ]

    def validate_slug(self, value):
        if Category.objects.filter(slug=value).exists():
            raise serializers.ValidationError("This slug already exists.")
        return value

    def create(self, validated_data):
        image = validated_data.pop('image', None)
        category = Category.objects.create(**validated_data)
        if image:
            category.image = image
            category.save()
        return category


class CategoryListSerializer(serializers.ModelSerializer):
    image  = serializers.SerializerMethodField()
    parent = serializers.SerializerMethodField()

    class Meta:
        model  = Category
        fields = [
            'id', 'name', 'slug', 'image', 'parent',
            'is_active', 'order', 'deleted_at', 'created_at',
        ]

    def get_image(self, obj):
        if obj.image:
            return obj.image.url
        return None

    def get_parent(self, obj):
        if obj.parent:
            return {'id': obj.parent.id, 'name': obj.parent.name}
        return None


class CategoryDetailSerializer(serializers.ModelSerializer):
    image    = serializers.SerializerMethodField()
    parent   = serializers.SerializerMethodField()
    children = serializers.SerializerMethodField()
    user       = serializers.SerializerMethodField()
    updated_by = serializers.SerializerMethodField()
    deleted_by = serializers.SerializerMethodField()

    class Meta:
        model  = Category
        fields = [
            'id', 'user', 'name', 'slug', 'image', 'parent', 'children',
            'is_active', 'order', 'meta_title', 'meta_description',
            'updated_by', 'deleted_by',
            'created_at', 'updated_at', 'deleted_at',
        ]

    def get_image(self, obj):
        if obj.image:
            return obj.image.url
        return None

    def get_parent(self, obj):
        if obj.parent:
            return {'id': obj.parent.id, 'name': obj.parent.name}
        return None

    def get_children(self, obj):
        qs = obj.children.filter(deleted_at__isnull=True)
        return [{'id': c.id, 'name': c.name, 'slug': c.slug} for c in qs]

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


class CategoryUpdateSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(required=False, allow_null=True)

    class Meta:
        model  = Category
        fields = [
            'name', 'slug', 'image', 'parent',
            'is_active', 'order', 'meta_title', 'meta_description',
        ]

    def validate_slug(self, value):
        qs = Category.objects.filter(slug=value).exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("This slug already exists.")
        return value

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance
