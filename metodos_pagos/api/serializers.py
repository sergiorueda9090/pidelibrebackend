from rest_framework import serializers
from metodos_pagos.models import PaymentMethod


class PaymentMethodSerializer(serializers.ModelSerializer):
    logo = serializers.FileField(required=False, allow_null=True)

    class Meta:
        model = PaymentMethod
        fields = [
            'provider', 'name', 'description', 'logo',
            'public_key', 'access_token', 'secret_key', 'client_id',
            'webhook_secret', 'extra_config',
            'environment', 'is_active', 'order',
            'currency', 'supported_countries',
        ]

    def create(self, validated_data):
        logo = validated_data.pop('logo', None)
        payment_method = PaymentMethod.objects.create(**validated_data)
        if logo:
            payment_method.logo = logo
            payment_method.save()
        return payment_method


class PaymentMethodListSerializer(serializers.ModelSerializer):
    logo = serializers.SerializerMethodField()
    provider_display = serializers.CharField(source='get_provider_display', read_only=True)
    environment_display = serializers.CharField(source='get_environment_display', read_only=True)

    class Meta:
        model = PaymentMethod
        fields = [
            'id', 'provider', 'provider_display', 'name', 'description', 'logo',
            'environment', 'environment_display', 'is_active', 'order',
            'currency', 'supported_countries',
            'deleted_at', 'created_at',
        ]

    def get_logo(self, obj):
        if obj.logo:
            return obj.logo.url
        return None


class PaymentMethodDetailSerializer(serializers.ModelSerializer):
    logo = serializers.SerializerMethodField()
    user = serializers.SerializerMethodField()
    provider_display = serializers.CharField(source='get_provider_display', read_only=True)
    environment_display = serializers.CharField(source='get_environment_display', read_only=True)

    class Meta:
        model = PaymentMethod
        fields = [
            'id', 'user', 'provider', 'provider_display', 'name', 'description', 'logo',
            'public_key', 'access_token', 'secret_key', 'client_id',
            'webhook_secret', 'extra_config',
            'environment', 'environment_display', 'is_active', 'order',
            'currency', 'supported_countries',
            'created_at', 'updated_at', 'deleted_at',
        ]

    def get_logo(self, obj):
        if obj.logo:
            return obj.logo.url
        return None

    def get_user(self, obj):
        return {'id': obj.user.id, 'username': obj.user.username}


class PaymentMethodUpdateSerializer(serializers.ModelSerializer):
    logo = serializers.FileField(required=False, allow_null=True)

    class Meta:
        model = PaymentMethod
        fields = [
            'provider', 'name', 'description', 'logo',
            'public_key', 'access_token', 'secret_key', 'client_id',
            'webhook_secret', 'extra_config',
            'environment', 'is_active', 'order',
            'currency', 'supported_countries',
        ]

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance
