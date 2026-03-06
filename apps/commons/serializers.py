from rest_framework import serializers


class LocationInputSerializer(serializers.Serializer):
    street_name = serializers.CharField()
    lat = serializers.CharField()
    lng = serializers.CharField()
