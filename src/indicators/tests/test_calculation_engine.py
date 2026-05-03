from django.test import TestCase

from emissions.models import EmissionFactor
from indicators.models import Indicator, IndicatorDependency, IndicatorValue
from indicators.services import calculate_indicator_value
from organizations.models import Organization
from submissions.models import ReportingPeriod


class CalculationEngineTests(TestCase):
    def setUp(self):
        self.org = Organization.objects.create(name="Calc Org", sector="manufacturing", country="NG")
        self.period = ReportingPeriod.objects.create(
            organization=self.org,
            name="2026",
            period_type=ReportingPeriod.PeriodType.ANNUAL,
            year=2026,
            is_active=True,
        )

        self.input_diesel = Indicator.objects.create(
            code="S1-DIESEL-CALC",
            name="Diesel",
            pillar=Indicator.Pillar.ENVIRONMENTAL,
            data_type=Indicator.DataType.NUMBER,
            indicator_type=Indicator.IndicatorType.INPUT,
            collection_method=Indicator.CollectionMethod.ACTIVITY,
            unit="litres",
        )
        self.input_lpg = Indicator.objects.create(
            code="S1-LPG-CALC",
            name="LPG",
            pillar=Indicator.Pillar.ENVIRONMENTAL,
            data_type=Indicator.DataType.NUMBER,
            indicator_type=Indicator.IndicatorType.INPUT,
            collection_method=Indicator.CollectionMethod.ACTIVITY,
            unit="kg",
        )

        self.scope1 = Indicator.objects.create(
            code="ENV-S1-CALC",
            name="Scope 1",
            pillar=Indicator.Pillar.ENVIRONMENTAL,
            data_type=Indicator.DataType.NUMBER,
            indicator_type=Indicator.IndicatorType.DERIVED,
            collection_method=Indicator.CollectionMethod.DIRECT,
            unit="tCO2e",
        )
        self.scope2 = Indicator.objects.create(
            code="ENV-S2-CALC",
            name="Scope 2",
            pillar=Indicator.Pillar.ENVIRONMENTAL,
            data_type=Indicator.DataType.NUMBER,
            indicator_type=Indicator.IndicatorType.DERIVED,
            collection_method=Indicator.CollectionMethod.DIRECT,
            unit="tCO2e",
        )
        self.total = Indicator.objects.create(
            code="ENV-TOTAL-CALC",
            name="Total Emissions",
            pillar=Indicator.Pillar.ENVIRONMENTAL,
            data_type=Indicator.DataType.NUMBER,
            indicator_type=Indicator.IndicatorType.DERIVED,
            collection_method=Indicator.CollectionMethod.DIRECT,
            unit="tCO2e",
        )

        from compliance.models import FrameworkRequirement, IndicatorFrameworkMapping
        from organizations.models import RegulatoryFramework

        fw = RegulatoryFramework.objects.create(code="CALC-FW", name="Calc FW", jurisdiction=RegulatoryFramework.Jurisdiction.INTERNATIONAL)
        req = FrameworkRequirement.objects.create(
            framework=fw,
            code="CALC-REQ",
            title="Calc Req",
            pillar=FrameworkRequirement.Pillar.ENVIRONMENTAL,
            is_mandatory=True,
        )
        IndicatorFrameworkMapping.objects.create(
            indicator=self.scope1,
            framework=fw,
            requirement=req,
            mapping_type=IndicatorFrameworkMapping.MappingType.PRIMARY,
            is_primary=True,
            is_active=True,
        )

        IndicatorDependency.objects.create(
            parent_indicator=self.scope1,
            child_indicator=self.input_diesel,
            relationship_type=IndicatorDependency.RelationshipType.CONVERSION,
            is_active=True,
        )
        IndicatorDependency.objects.create(
            parent_indicator=self.scope1,
            child_indicator=self.input_lpg,
            relationship_type=IndicatorDependency.RelationshipType.CONVERSION,
            is_active=True,
        )
        IndicatorDependency.objects.create(
            parent_indicator=self.total,
            child_indicator=self.scope1,
            relationship_type=IndicatorDependency.RelationshipType.AGGREGATION,
            is_active=True,
        )
        IndicatorDependency.objects.create(
            parent_indicator=self.total,
            child_indicator=self.scope2,
            relationship_type=IndicatorDependency.RelationshipType.AGGREGATION,
            is_active=True,
        )

        EmissionFactor.objects.create(
            activity_type_id=None,
            indicator=self.input_diesel,
            country=None,
            year=2026,
            factor=2.68,
            factor_value=2.68,
            unit="kgCO2e/litre",
            unit_input="litres",
            unit_output="kgCO2e",
        )
        EmissionFactor.objects.create(
            activity_type_id=None,
            indicator=self.input_lpg,
            country=None,
            year=2026,
            factor=3.00,
            factor_value=3.00,
            unit="kgCO2e/kg",
            unit_input="kg",
            unit_output="kgCO2e",
        )

        IndicatorValue.objects.create(
            organization=self.org,
            indicator=self.input_diesel,
            reporting_period=self.period,
            facility=None,
            value=100,
        )
        IndicatorValue.objects.create(
            organization=self.org,
            indicator=self.input_lpg,
            reporting_period=self.period,
            facility=None,
            value=10,
        )
        IndicatorValue.objects.create(
            organization=self.org,
            indicator=self.scope2,
            reporting_period=self.period,
            facility=None,
            value=50,
        )

    def test_calculate_primary_indicator_uses_child_and_factor(self):
        value = calculate_indicator_value(indicator=self.scope1, period=self.period, org=self.org)
        self.assertAlmostEqual(value, 298.0, places=3)

    def test_calculate_derived_indicator_sums_primary_indicators(self):
        calculate_indicator_value(indicator=self.scope1, period=self.period, org=self.org)
        total = calculate_indicator_value(indicator=self.total, period=self.period, org=self.org)
        self.assertAlmostEqual(total, 348.0, places=3)
