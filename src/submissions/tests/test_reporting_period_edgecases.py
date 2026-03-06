from django.test import TestCase
from django.core.exceptions import ValidationError
from accounts.models.user import User
from organizations.models.organization import Organization
from submissions.models import ReportingPeriod, DataSubmission
from indicators.models import Indicator


class ReportingPeriodEdgeCasesTest(TestCase):
    def setUp(self):
        self.org = Organization.objects.create(name="EdgeOrg", sector="services", country="US")
        self.user = User.objects.create_user(username="u_edge", email="edge@example.com", password="pass")

    def test_delete_blocked_when_submissions_exist(self):
        ind = Indicator.objects.create(code="EC1", name="E1", pillar="ENV", data_type=Indicator.DataType.NUMBER)
        rp = ReportingPeriod.objects.create(organization=self.org, year=2025)
        DataSubmission.objects.create(organization=self.org, indicator=ind, reporting_period=rp, value_number=1.0)

        with self.assertRaises(ValidationError):
            rp.delete()

    def test_lock_sets_fields(self):
        rp = ReportingPeriod.objects.create(organization=self.org, year=2025)
        rp.lock(by_user=self.user)
        self.assertEqual(rp.status, ReportingPeriod.Status.LOCKED)
        self.assertIsNotNone(rp.locked_at)
        self.assertEqual(rp.locked_by, self.user)
