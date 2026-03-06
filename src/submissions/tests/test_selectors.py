from django.test import TestCase

from organizations.models.organization import Organization
from indicators.models import Indicator, OrganizationIndicator
from submissions.selectors.queries import get_period_submissions
from submissions.models import ReportingPeriod


class SelectorTests(TestCase):
    def setUp(self):
        self.org = Organization.objects.create(name="SelOrg", sector="finance", country="NG")
        self.ind1 = Indicator.objects.create(code="S1", name="S1", pillar="ENV", data_type=Indicator.DataType.NUMBER)
        self.ind2 = Indicator.objects.create(code="S2", name="S2", pillar="SOC", data_type=Indicator.DataType.BOOLEAN)
        OrganizationIndicator.objects.create(organization=self.org, indicator=self.ind1, is_active=True)
        OrganizationIndicator.objects.create(organization=self.org, indicator=self.ind2, is_active=True)
        self.period = ReportingPeriod.objects.create(organization=self.org, year=2025)

    def test_get_period_submissions_structure(self):
        results = get_period_submissions(self.org, self.period)
        self.assertIsInstance(results, list)
        for r in results:
            self.assertIn('indicator', r)
            self.assertIn('is_required_effective', r)
            self.assertIn('is_active_effective', r)
            self.assertIn('submission', r)
