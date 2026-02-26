from rest_framework import serializers
from attribute.models import Attribute


class AttributeSerializer(serializers.ModelSerializer):
    """Usado en creación."""

    class Meta:
        model  = Attribute
        fields = ['name']

    def validate_name(self, value):
        if Attribute.objects.filter(name__iexact=value).exists():
            raise serializers.ValidationError("An attribute with this name already exists.")
        return value


class AttributeListSerializer(serializers.ModelSerializer):
    """Usado en el listado paginado."""

    class Meta:
        model  = Attribute
        fields = ['id', 'name', 'created_at', 'deleted_at']


class AttributeDetailSerializer(serializers.ModelSerializer):
    """Usado en create/get-by-id para devolver el registro completo."""

    class Meta:
        model  = Attribute
        fields = ['id', 'name', 'created_at', 'updated_at', 'deleted_at']


class AttributeUpdateSerializer(serializers.ModelSerializer):
    """Usado en actualización parcial."""

    class Meta:
        model  = Attribute
        fields = ['name']

    def validate_name(self, value):
        qs = Attribute.objects.filter(name__iexact=value).exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("An attribute with this name already exists.")
        return value

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance
