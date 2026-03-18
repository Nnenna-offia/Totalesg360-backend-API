from django.test import TestCase

from django.contrib.auth import get_user_model
from organizations.models import Organization, Facility
from roles.models import Role

from targets.models import TargetGoal, TargetMilestone
from indicators.models import Indicator
from organizations.models.regulatory_framework import RegulatoryFramework
from submissions.models import ReportingPeriod, DataSubmission

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
        # add submission value
        period = ReportingPeriod.objects.create(organization=self.org, year=2023)
        DataSubmission.objects.create(organization=self.org, reporting_period=period, indicator=self.ind, value_number=1000.0)
        from targets.services.target_progress_service import calculate_target_progress
        res = calculate_target_progress(self.goal)
        self.assertTrue(isinstance(res['progress_percent'], int))
