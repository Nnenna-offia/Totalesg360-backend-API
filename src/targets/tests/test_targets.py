from django.test import TestCase
from datetime import date

from django.contrib.auth import get_user_model
from organizations.models import Organization, Facility
from roles.models import Role

from targets.models import TargetGoal, TargetMilestone
from indicators.models import Indicator, IndicatorValue
from submissions.models import ReportingPeriod

User = get_user_model()


class TargetTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='t', email='t@example.com', password='pass')
        self.org = Organization.objects.create(name='Org T')
        self.role = Role.objects.filter(code='org_owner').first()

        self.ind = Indicator.objects.create(code='S1', name='Scope 1', pillar=Indicator.Pillar.ENVIRONMENTAL, data_type=Indicator.DataType.NUMBER)

        self.goal = TargetGoal.objects.create(
            organization=self.org,
            indicator=self.ind,
            name='Reduce S1',
            baseline_year=2022,
            baseline_value=1200.0,
            target_year=2030,
            target_value=800.0,
            direction=TargetGoal.Direction.DECREASE,
            created_by=self.user,
        )

        TargetMilestone.objects.create(goal=self.goal, year=2025, target_value=1100.0)
        TargetMilestone.objects.create(goal=self.goal, year=2027, target_value=950.0)

    def test_progress_no_submissions(self):
        from targets.services.target_progress_service import calculate_target_progress
        res = calculate_target_progress(self.goal)
        self.assertEqual(res['progress_percent'], 0)

    def test_progress_with_submission(self):
        # add aggregated indicator value
        period = ReportingPeriod.objects.create(organization=self.org, year=2023)
        IndicatorValue.objects.create(organization=self.org, reporting_period=period, indicator=self.ind, value=1000.0)
        from targets.services.target_progress_service import calculate_target_progress
        res = calculate_target_progress(self.goal)
        self.assertTrue(isinstance(res['progress_percent'], int))

    def test_progress_aggregates_facility_values_in_active_period(self):
        period = ReportingPeriod.objects.create(
            organization=self.org,
            name='Jan 2023',
            period_type=ReportingPeriod.PeriodType.ANNUAL,
            year=2023,
            is_active=True,
        )
        IndicatorValue.objects.create(
            organization=self.org,
            reporting_period=period,
            indicator=self.ind,
            value=60.0,
            facility=None,
        )
        IndicatorValue.objects.create(
            organization=self.org,
            reporting_period=period,
            indicator=self.ind,
            value=40.0,
            facility=None,
            metadata={'source': 'second-aggregate-row'},
        )

        from targets.services.target_progress_service import calculate_target_progress
        res = calculate_target_progress(self.goal)
        self.assertEqual(res['current_value'], 100.0)

    def test_progress_uses_goal_frequency_active_period_only(self):
        monthly = ReportingPeriod.objects.filter(
            organization=self.org,
            period_type=ReportingPeriod.PeriodType.MONTHLY,
            is_active=True,
        ).first()
        if monthly is None:
            monthly = ReportingPeriod.objects.create(
                organization=self.org,
                name='Jan 2023',
                period_type=ReportingPeriod.PeriodType.MONTHLY,
                start_date=date(2023, 1, 1),
                end_date=date(2023, 1, 31),
                is_active=True,
            )
        annual = ReportingPeriod.objects.filter(
            organization=self.org,
            period_type=ReportingPeriod.PeriodType.ANNUAL,
            is_active=True,
        ).first()
        if annual is None:
            annual = ReportingPeriod.objects.create(
                organization=self.org,
                name='2023',
                period_type=ReportingPeriod.PeriodType.ANNUAL,
                start_date=date(2023, 1, 1),
                end_date=date(2023, 12, 31),
                is_active=True,
            )

        IndicatorValue.objects.create(organization=self.org, reporting_period=monthly, indicator=self.ind, value=999.0)
        IndicatorValue.objects.create(organization=self.org, reporting_period=annual, indicator=self.ind, value=1000.0)

        from targets.services.target_progress_service import calculate_target_progress
        res = calculate_target_progress(self.goal)
        self.assertEqual(res['current_value'], 1000.0)
