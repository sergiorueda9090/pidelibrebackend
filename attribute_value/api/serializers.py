from rest_framework import serializers
from attribute.models import Attribute
from attribute_value.models import AttributeValue


class AttributeValueSerializer(serializers.ModelSerializer):
    """Usado en creación."""
    attribute = serializers.PrimaryKeyRelatedField(queryset=Attribute.objects.all())
    color_hex = serializers.CharField(max_length=7, required=False, allow_null=True, allow_blank=True)

    class Meta:
        model  = AttributeValue
        fields = ['attribute', 'value', 'color_hex', 'order']

    def validate(self, data):
        attribute = data.get('attribute')
        value     = data.get('value', '').strip()
        if AttributeValue.objects.filter(attribute=attribute, value__iexact=value).exists():
            raise serializers.ValidationError(
                {'value': 'This value already exists for the selected attribute.'}
            )
        return data


class AttributeValueListSerializer(serializers.ModelSerializer):
    """Usado en el listado paginado."""
    attribute = serializers.SerializerMethodField()

    class Meta:
        model  = AttributeValue
        fields = ['id', 'attribute', 'value', 'color_hex', 'order', 'created_at', 'deleted_at']

    def get_attribute(self, obj):
        return {'id': obj.attribute.id, 'name': obj.attribute.name}


class AttributeValueDetailSerializer(serializers.ModelSerializer):
    """Usado en create/get-by-id para devolver el registro completo."""
    attribute = serializers.SerializerMethodField()
    user      = serializers.SerializerMethodField()

    class Meta:
        model  = AttributeValue
        fields = [
            'id', 'user', 'attribute', 'value', 'color_hex', 'order',
            'created_at', 'updated_at', 'deleted_at',
        ]

    def get_attribute(self, obj):
        return {'id': obj.attribute.id, 'name': obj.attribute.name}

    def get_user(self, obj):
        return {'id': obj.user.id, 'username': obj.user.username}


class AttributeValueUpdateSerializer(serializers.ModelSerializer):
    """Usado en actualización parcial. El atributo no se puede cambiar."""
    color_hex = serializers.CharField(max_length=7, required=False, allow_null=True, allow_blank=True)

    class Meta:
        model  = AttributeValue
        fields = ['value', 'color_hex', 'order']

    def validate_value(self, value):
        qs = AttributeValue.objects.filter(
            attribute=self.instance.attribute,
            value__iexact=value
        ).exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError('This value already exists for the selected attribute.')
        return value

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance
