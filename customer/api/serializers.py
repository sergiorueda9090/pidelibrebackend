from rest_framework import serializers
from customer.models import Customer, CustomerAddress
from gender.models import Gender


# ── Direcciones ───────────────────────────────────────────────────────────────
class CustomerAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model  = CustomerAddress
        fields = ['id', 'address', 'city', 'state', 'country', 'postal_code', 'created_at']


class CustomerAddressCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model  = CustomerAddress
        fields = ['address', 'city', 'state', 'country', 'postal_code']


# ── Creación de cliente ───────────────────────────────────────────────────────
class CustomerSerializer(serializers.ModelSerializer):
    gender = serializers.PrimaryKeyRelatedField(
        queryset=Gender.objects.all(), required=False, allow_null=True
    )

    class Meta:
        model  = Customer
        fields = [
            'first_name', 'last_name', 'email', 'phone',
            'document_number', 'date_of_birth', 'gender', 'is_active',
        ]

    def validate_email(self, value):
        if Customer.objects.filter(email=value).exists():
            raise serializers.ValidationError("A customer with this email already exists.")
        return value


# ── Listado paginado ──────────────────────────────────────────────────────────
class CustomerListSerializer(serializers.ModelSerializer):
    gender = serializers.SerializerMethodField()

    class Meta:
        model  = Customer
        fields = [
            'id', 'first_name', 'last_name', 'email', 'phone',
            'document_number', 'gender', 'is_active',
            'deleted_at', 'created_at',
        ]

    def get_gender(self, obj):
        if obj.gender:
            return {'id': obj.gender.id, 'name': obj.gender.name}
        return None


# ── Detalle completo ──────────────────────────────────────────────────────────
class CustomerDetailSerializer(serializers.ModelSerializer):
    gender    = serializers.SerializerMethodField()
    addresses = serializers.SerializerMethodField()

    class Meta:
        model  = Customer
        fields = [
            'id', 'first_name', 'last_name', 'email', 'phone',
            'document_number', 'date_of_birth', 'gender', 'is_active',
            'addresses',
            'created_at', 'updated_at', 'deleted_at',
        ]

    def get_gender(self, obj):
        if obj.gender:
            return {'id': obj.gender.id, 'name': obj.gender.name}
        return None

    def get_addresses(self, obj):
        return CustomerAddressSerializer(obj.addresses.all(), many=True).data


# ── Actualización parcial ─────────────────────────────────────────────────────
class CustomerUpdateSerializer(serializers.ModelSerializer):
    gender = serializers.PrimaryKeyRelatedField(
        queryset=Gender.objects.all(), required=False, allow_null=True
    )

    class Meta:
        model  = Customer
        fields = [
            'first_name', 'last_name', 'email', 'phone',
            'document_number', 'date_of_birth', 'gender', 'is_active',
        ]

    def validate_email(self, value):
        qs = Customer.objects.filter(email=value).exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("A customer with this email already exists.")
        return value

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance
