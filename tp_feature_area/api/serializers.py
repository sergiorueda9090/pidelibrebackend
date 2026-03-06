from rest_framework import serializers
from tp_feature_area.models import TpFeatureArea


class TpFeatureAreaSerializer(serializers.ModelSerializer):
    class Meta:
        model  = TpFeatureArea
        fields = ['icon', 'title', 'description', 'order', 'is_active']

    def create(self, validated_data):
        return TpFeatureArea.objects.create(**validated_data)


class TpFeatureAreaListSerializer(serializers.ModelSerializer):
    class Meta:
        model  = TpFeatureArea
        fields = ['id', 'icon', 'title', 'description', 'order', 'is_active', 'deleted_at', 'created_at']


class TpFeatureAreaDetailSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()

    class Meta:
        model  = TpFeatureArea
        fields = [
            'id', 'user', 'icon', 'title', 'description', 'order', 'is_active',
            'created_at', 'updated_at', 'deleted_at',
        ]

    def get_user(self, obj):
        return {'id': obj.user.id, 'username': obj.user.username}


class TpFeatureAreaUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model  = TpFeatureArea
        fields = ['icon', 'title', 'description', 'order', 'is_active']

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance
