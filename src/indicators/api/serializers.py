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
            "indicator_type",
            "emission_factor",
            "calculation_method",
            "collection_method",
            "is_active",
            "version",
        ]
        read_only_fields = ["id"]
