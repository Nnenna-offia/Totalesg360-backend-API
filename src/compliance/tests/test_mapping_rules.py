from django.test import TestCase

from compliance.api.serializers import (
    CreateIndicatorFrameworkMappingSerializer,
    IndicatorFrameworkMappingSerializer,
)
from compliance.models import FrameworkRequirement, IndicatorFrameworkMapping
from indicators.models import Indicator, IndicatorValue
from organizations.models import Organization, RegulatoryFramework
from submissions.models import ReportingPeriod


class IndicatorFrameworkMappingRulesTests(TestCase):
    def setUp(self):
        self.framework = RegulatoryFramework.objects.create(
            code="MR-FW",
            name="Mapping Rules Framework",
            jurisdiction=RegulatoryFramework.Jurisdiction.INTERNATIONAL,
        )
        self.requirement = FrameworkRequirement.objects.create(
            framework=self.framework,
            code="MR-REQ-1",
            title="Requirement",
            pillar=FrameworkRequirement.Pillar.ENVIRONMENTAL,
            is_mandatory=True,
        )

        self.input_indicator = Indicator.objects.create(
            code="MR-INP",
            name="Input",
            pillar=Indicator.Pillar.ENVIRONMENTAL,
            data_type=Indicator.DataType.NUMBER,
            indicator_type=Indicator.IndicatorType.INPUT,
        )
        self.derived_indicator = Indicator.objects.create(
            code="MR-DER",
            name="Derived",
            pillar=Indicator.Pillar.ENVIRONMENTAL,
            data_type=Indicator.DataType.NUMBER,
            indicator_type=Indicator.IndicatorType.DERIVED,
            collection_method=Indicator.CollectionMethod.DIRECT,
        )

    def test_primary_mapping_requires_derived_indicator(self):
        serializer = CreateIndicatorFrameworkMappingSerializer(
            data={
                "indicator": str(self.input_indicator.id),
                "framework": str(self.framework.id),
                "requirement": str(self.requirement.id),
                "mapping_type": IndicatorFrameworkMapping.MappingType.PRIMARY,
                "is_primary": True,
                "is_active": True,
            }
        )
        self.assertFalse(serializer.is_valid())

    def test_secondary_mapping_requires_existing_primary(self):
        serializer = CreateIndicatorFrameworkMappingSerializer(
            data={
                "indicator": str(self.input_indicator.id),
                "framework": str(self.framework.id),
                "requirement": str(self.requirement.id),
                "mapping_type": IndicatorFrameworkMapping.MappingType.SECONDARY,
                "is_primary": False,
                "is_active": True,
            }
        )
        self.assertFalse(serializer.is_valid())

    def test_dynamic_coverage_uses_indicator_values(self):
        mapping = IndicatorFrameworkMapping.objects.create(
            indicator=self.derived_indicator,
            framework=self.framework,
            requirement=self.requirement,
            mapping_type=IndicatorFrameworkMapping.MappingType.PRIMARY,
            is_primary=True,
            is_active=True,
        )

        serialized = IndicatorFrameworkMappingSerializer(mapping).data
        self.assertEqual(serialized["coverage_percent"], 0)
        self.assertEqual(serialized["coverage_status"], "not_started")

        org = Organization.objects.create(name="Coverage Org", sector="finance", country="NG")
        period = ReportingPeriod.objects.create(
            organization=org,
            name="2026",
            period_type=ReportingPeriod.PeriodType.ANNUAL,
            year=2026,
            is_active=True,
        )
        IndicatorValue.objects.create(
            organization=org,
            indicator=self.derived_indicator,
            reporting_period=period,
            value=1,
        )

        serialized = IndicatorFrameworkMappingSerializer(mapping).data
        self.assertEqual(serialized["coverage_percent"], 100)
        self.assertEqual(serialized["coverage_status"], "full")
