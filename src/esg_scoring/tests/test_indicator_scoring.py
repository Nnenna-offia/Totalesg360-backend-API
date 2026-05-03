from django.test import TestCase

from esg_scoring.models import IndicatorScore
from esg_scoring.services.indicator_scoring import calculate_indicator_score
from esg_scoring.services.pillar_scoring import calculate_pillar_score
from indicators.models import Indicator, IndicatorValue
from organizations.models import Organization
from submissions.models import ReportingPeriod
from targets.models import TargetGoal


class IndicatorScoringRegressionTests(TestCase):
    def setUp(self):
        self.org = Organization.objects.create(name="Score Org", sector="manufacturing", country="NG")
        self.period = ReportingPeriod.objects.create(
            organization=self.org,
            name="2026",
            period_type=ReportingPeriod.PeriodType.ANNUAL,
            year=2026,
            is_active=True,
        )
        self.indicator = Indicator.objects.create(
            code="SCORE-ENV-1",
            name="Scope 1 Emissions",
            pillar=Indicator.Pillar.ENVIRONMENTAL,
            data_type=Indicator.DataType.NUMBER,
            indicator_type=Indicator.IndicatorType.DERIVED,
            collection_method=Indicator.CollectionMethod.DIRECT,
        )

    def test_calculate_indicator_score_uses_indicator_value_and_current_target_fields(self):
        IndicatorValue.objects.create(
            organization=self.org,
            indicator=self.indicator,
            reporting_period=self.period,
            facility=None,
            value=80.0,
        )
        TargetGoal.objects.create(
            organization=self.org,
            indicator=self.indicator,
            name="Reduce emissions",
            reporting_frequency=TargetGoal.ReportingFrequency.ANNUAL,
            baseline_year=2025,
            baseline_value=100.0,
            target_year=2030,
            target_value=60.0,
            direction=TargetGoal.Direction.DECREASE,
        )

        score = calculate_indicator_score(self.org, self.indicator, self.period)

        self.assertEqual(score.status, IndicatorScore.ScoreStatus.AT_RISK)
        self.assertEqual(score.value, 80.0)
        self.assertEqual(score.baseline, 100.0)
        self.assertEqual(score.target, 60.0)
        self.assertAlmostEqual(score.progress, 50.0, places=2)

    def test_calculate_pillar_score_uses_score_status_enum(self):
        IndicatorScore.objects.create(
            organization=self.org,
            indicator=self.indicator,
            reporting_period=self.period,
            score=80.0,
            value=80.0,
            baseline=100.0,
            target=60.0,
            progress=80.0,
            status=IndicatorScore.ScoreStatus.ACHIEVED,
            calculation_method="test",
        )

        pillar_score = calculate_pillar_score(
            organization=self.org,
            pillar=Indicator.Pillar.ENVIRONMENTAL,
            reporting_period=self.period,
        )

        self.assertIsNotNone(pillar_score)
        self.assertEqual(pillar_score.indicator_count, 1)
        self.assertEqual(pillar_score.on_track_count, 1)
        self.assertEqual(pillar_score.at_risk_count, 0)