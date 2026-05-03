from unittest.mock import patch

from django.test import TestCase

from compliance.models import FrameworkRequirement, IndicatorFrameworkMapping
from emissions.models import EmissionFactor
from indicators.models import Indicator, IndicatorDependency, IndicatorValue
from indicators.services.calculation_engine import get_affected_indicators
from organizations.models import Organization, RegulatoryFramework
from submissions.models import ReportingPeriod
from targets.models import TargetEvaluation, TargetGoal


class _FakeAsyncResult:
    def then(self, *args, **kwargs):
        return self


class AffectedIndicatorsOptimizationTests(TestCase):
    def setUp(self):
        self.diesel = Indicator.objects.create(
            code="TEST-DIESEL-AFFECTED",
            name="Diesel",
            pillar=Indicator.Pillar.ENVIRONMENTAL,
            data_type=Indicator.DataType.NUMBER,
            indicator_type=Indicator.IndicatorType.INPUT,
            collection_method=Indicator.CollectionMethod.ACTIVITY,
        )
        self.scope1 = Indicator.objects.create(
            code="TEST-SCOPE1-AFFECTED",
            name="Scope 1",
            pillar=Indicator.Pillar.ENVIRONMENTAL,
            data_type=Indicator.DataType.NUMBER,
            indicator_type=Indicator.IndicatorType.DERIVED,
            collection_method=Indicator.CollectionMethod.DIRECT,
        )
        self.total = Indicator.objects.create(
            code="TEST-TOTAL-AFFECTED",
            name="Total Emissions",
            pillar=Indicator.Pillar.ENVIRONMENTAL,
            data_type=Indicator.DataType.NUMBER,
            indicator_type=Indicator.IndicatorType.DERIVED,
            collection_method=Indicator.CollectionMethod.DIRECT,
        )

        IndicatorDependency.objects.create(
            parent_indicator=self.scope1,
            child_indicator=self.diesel,
            relationship_type=IndicatorDependency.RelationshipType.CONVERSION,
            is_active=True,
        )
        IndicatorDependency.objects.create(
            parent_indicator=self.total,
            child_indicator=self.scope1,
            relationship_type=IndicatorDependency.RelationshipType.AGGREGATION,
            is_active=True,
        )

    def test_get_affected_indicators_resolves_chain_in_two_queries(self):
        with self.assertNumQueries(2):
            affected = get_affected_indicators(self.diesel)
            codes = {indicator.code for indicator in affected}

        self.assertEqual(
            codes,
            {"TEST-DIESEL-AFFECTED", "TEST-SCOPE1-AFFECTED", "TEST-TOTAL-AFFECTED"},
        )


class IndicatorPipelineSignalIntegrationTests(TestCase):
    def setUp(self):
        self.org = Organization.objects.create(name="Pipeline Org", sector="manufacturing", country="NG")
        self.period = ReportingPeriod.objects.create(
            organization=self.org,
            name="2026",
            period_type=ReportingPeriod.PeriodType.ANNUAL,
            year=2026,
            is_active=True,
        )

        self.diesel = Indicator.objects.create(
            code="PIPE-DIESEL",
            name="Diesel",
            pillar=Indicator.Pillar.ENVIRONMENTAL,
            data_type=Indicator.DataType.NUMBER,
            indicator_type=Indicator.IndicatorType.INPUT,
            collection_method=Indicator.CollectionMethod.ACTIVITY,
            unit="litres",
        )
        self.scope1 = Indicator.objects.create(
            code="PIPE-SCOPE1",
            name="Scope 1",
            pillar=Indicator.Pillar.ENVIRONMENTAL,
            data_type=Indicator.DataType.NUMBER,
            indicator_type=Indicator.IndicatorType.DERIVED,
            collection_method=Indicator.CollectionMethod.DIRECT,
            unit="tCO2e",
        )
        self.scope2 = Indicator.objects.create(
            code="PIPE-SCOPE2",
            name="Scope 2",
            pillar=Indicator.Pillar.ENVIRONMENTAL,
            data_type=Indicator.DataType.NUMBER,
            indicator_type=Indicator.IndicatorType.DERIVED,
            collection_method=Indicator.CollectionMethod.DIRECT,
            unit="tCO2e",
        )
        self.total = Indicator.objects.create(
            code="PIPE-TOTAL",
            name="Total Emissions",
            pillar=Indicator.Pillar.ENVIRONMENTAL,
            data_type=Indicator.DataType.NUMBER,
            indicator_type=Indicator.IndicatorType.DERIVED,
            collection_method=Indicator.CollectionMethod.DIRECT,
            unit="tCO2e",
        )

        framework = RegulatoryFramework.objects.create(
            code="PIPE-FW",
            name="Pipeline Framework",
            jurisdiction=RegulatoryFramework.Jurisdiction.INTERNATIONAL,
        )
        requirement = FrameworkRequirement.objects.create(
            framework=framework,
            code="PIPE-REQ",
            title="Pipeline Requirement",
            pillar=FrameworkRequirement.Pillar.ENVIRONMENTAL,
            is_mandatory=True,
        )
        IndicatorFrameworkMapping.objects.create(
            indicator=self.scope1,
            framework=framework,
            requirement=requirement,
            mapping_type=IndicatorFrameworkMapping.MappingType.PRIMARY,
            is_primary=True,
            is_active=True,
        )

        IndicatorDependency.objects.create(
            parent_indicator=self.scope1,
            child_indicator=self.diesel,
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
            indicator=self.diesel,
            country=None,
            year=2026,
            factor=2.68,
            factor_value=2.68,
            unit="kgCO2e/litre",
            unit_input="litres",
            unit_output="kgCO2e",
        )

        IndicatorValue.objects.bulk_create(
            [
                IndicatorValue(
                    organization=self.org,
                    indicator=self.scope2,
                    reporting_period=self.period,
                    facility=None,
                    value=50.0,
                )
            ]
        )

        self.scope1_target = TargetGoal.objects.create(
            organization=self.org,
            indicator=self.scope1,
            name="Reduce Scope 1",
            baseline_year=2025,
            baseline_value=300.0,
            target_year=2030,
            target_value=200.0,
            direction=TargetGoal.Direction.DECREASE,
        )
        self.total_target = TargetGoal.objects.create(
            organization=self.org,
            indicator=self.total,
            name="Reduce Total Emissions",
            baseline_year=2025,
            baseline_value=400.0,
            target_year=2030,
            target_value=250.0,
            direction=TargetGoal.Direction.DECREASE,
        )

    @patch("esg_scoring.tasks.calculate_org_esg_score")
    @patch("esg_scoring.tasks.calculate_org_pillar_scores")
    @patch("esg_scoring.tasks.calculate_org_indicator_scores")
    def test_input_indicator_save_recalculates_parents_evaluates_relevant_targets_once(
        self,
        indicator_task,
        pillar_task,
        esg_task,
    ):
        async_result = _FakeAsyncResult()
        indicator_task.delay.return_value = async_result
        pillar_task.s.return_value = object()
        esg_task.s.return_value = object()

        IndicatorValue.objects.create(
            organization=self.org,
            indicator=self.diesel,
            reporting_period=self.period,
            facility=None,
            value=100.0,
        )

        scope1_value = IndicatorValue.objects.get(
            organization=self.org,
            indicator=self.scope1,
            reporting_period=self.period,
            facility=None,
        )
        total_value = IndicatorValue.objects.get(
            organization=self.org,
            indicator=self.total,
            reporting_period=self.period,
            facility=None,
        )

        self.assertAlmostEqual(scope1_value.value, 268.0, places=3)
        self.assertAlmostEqual(total_value.value, 318.0, places=3)

        evaluations = TargetEvaluation.objects.filter(reporting_period=self.period)
        self.assertEqual(evaluations.count(), 2)
        self.assertEqual(
            set(evaluations.values_list("target_id", flat=True)),
            {self.scope1_target.id, self.total_target.id},
        )

        self.assertEqual(indicator_task.delay.call_count, 1)
        self.assertEqual(pillar_task.s.call_count, 1)
        self.assertEqual(esg_task.s.call_count, 1)