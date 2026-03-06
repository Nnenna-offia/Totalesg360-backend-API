from rest_framework import serializers
from indicators.models import Indicator


class IndicatorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Indicator
        fields = [
            "id",
            "code",
            "name",
            "description",
            "pillar",
            "data_type",
            "unit",
            "is_active",
            "version",
        ]
        read_only_fields = ["id"]
