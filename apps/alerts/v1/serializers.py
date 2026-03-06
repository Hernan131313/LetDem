from rest_framework import serializers

from alerts.models import Alert


class AlertSerializer(serializers.ModelSerializer):
    """Serializer for alerts"""

    distance = serializers.SerializerMethodField()

    class Meta:
        model = Alert
        fields = ['type', 'road', 'latitude', 'longitude', 'direction', 'distance']

    def get_distance(self, instance):
        if not hasattr(instance, 'distance'):
            return None
        return round(instance.distance.m)
