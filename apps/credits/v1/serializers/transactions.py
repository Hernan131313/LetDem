from rest_framework import serializers


class ListTransactionsSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=6, decimal_places=2, source='format_amount')
    currency = serializers.CharField()
    source = serializers.CharField()
    created = serializers.DateTimeField()
