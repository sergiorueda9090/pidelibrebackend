from rest_framework import serializers
from footer.models import Footer


class FooterSerializer(serializers.ModelSerializer):
    logo = serializers.FileField(required=False, allow_null=True)
    payment_image = serializers.FileField(required=False, allow_null=True)

    class Meta:
        model = Footer
        fields = [
            'logo', 'description', 'facebook_url', 'twitter_url',
            'linkedin_url', 'instagram_url', 'phone', 'phone_label',
            'email', 'copyright_text', 'payment_image', 'is_active',
        ]

    def create(self, validated_data):
        logo = validated_data.pop('logo', None)
        payment_image = validated_data.pop('payment_image', None)
        footer = Footer.objects.create(**validated_data)
        if logo:
            footer.logo = logo
        if payment_image:
            footer.payment_image = payment_image
        if logo or payment_image:
            footer.save()
        return footer


class FooterListSerializer(serializers.ModelSerializer):
    logo = serializers.SerializerMethodField()
    payment_image = serializers.SerializerMethodField()

    class Meta:
        model = Footer
        fields = [
            'id', 'logo', 'description', 'facebook_url', 'twitter_url',
            'linkedin_url', 'instagram_url', 'phone', 'phone_label',
            'email', 'copyright_text', 'payment_image', 'is_active',
            'deleted_at', 'created_at',
        ]

    def get_logo(self, obj):
        if obj.logo:
            return obj.logo.url
        return None

    def get_payment_image(self, obj):
        if obj.payment_image:
            return obj.payment_image.url
        return None


class FooterDetailSerializer(serializers.ModelSerializer):
    logo = serializers.SerializerMethodField()
    payment_image = serializers.SerializerMethodField()
    user = serializers.SerializerMethodField()

    class Meta:
        model = Footer
        fields = [
            'id', 'user', 'logo', 'description', 'facebook_url', 'twitter_url',
            'linkedin_url', 'instagram_url', 'phone', 'phone_label',
            'email', 'copyright_text', 'payment_image', 'is_active',
            'created_at', 'updated_at', 'deleted_at',
        ]

    def get_logo(self, obj):
        if obj.logo:
            return obj.logo.url
        return None

    def get_payment_image(self, obj):
        if obj.payment_image:
            return obj.payment_image.url
        return None

    def get_user(self, obj):
        return {'id': obj.user.id, 'username': obj.user.username}


class FooterUpdateSerializer(serializers.ModelSerializer):
    logo = serializers.FileField(required=False, allow_null=True)
    payment_image = serializers.FileField(required=False, allow_null=True)

    class Meta:
        model = Footer
        fields = [
            'logo', 'description', 'facebook_url', 'twitter_url',
            'linkedin_url', 'instagram_url', 'phone', 'phone_label',
            'email', 'copyright_text', 'payment_image', 'is_active',
        ]

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance
