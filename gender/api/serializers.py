from rest_framework import serializers
from gender.models import Gender


class GenderSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Gender
        fields = ['name', 'slug', 'description']

    def validate_slug(self, value):
        if Gender.objects.filter(slug=value).exists():
            raise serializers.ValidationError("This slug already exists.")
        return value

    def create(self, validated_data):
        return Gender.objects.create(**validated_data)


class GenderListSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Gender
        fields = ['id', 'name', 'slug', 'deleted_at', 'created_at']


class GenderDetailSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()

    class Meta:
        model  = Gender
        fields = [
            'id', 'user', 'name', 'slug', 'description',
            'created_at', 'updated_at', 'deleted_at',
        ]

    def get_user(self, obj):
        return {'id': obj.user.id, 'username': obj.user.username}


class GenderUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Gender
        fields = ['name', 'slug', 'description']

    def validate_slug(self, value):
        qs = Gender.objects.filter(slug=value).exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("This slug already exists.")
        return value

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance
