from rest_framework import serializers


class EmissionSummarySerializer(serializers.Serializer):
    scope = serializers.CharField()
    total = serializers.DecimalField(max_digits=20, decimal_places=6)
