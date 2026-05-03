from django.test import TestCase

from organizations.models.organization import Organization
from indicators.models import Indicator, OrganizationIndicator
from compliance.models import FrameworkRequirement, IndicatorFrameworkMapping
from organizations.models import OrganizationFramework, RegulatoryFramework
from submissions.selectors.queries import get_period_submissions
from submissions.models import ReportingPeriod


class SelectorTests(TestCase):
    def setUp(self):
        self.org = Organization.objects.create(name="SelOrg", sector="finance", country="NG")
        self.ind1 = Indicator.objects.create(code="S1", name="S1", pillar="ENV", data_type=Indicator.DataType.NUMBER)
        self.ind2 = Indicator.objects.create(code="S2", name="S2", pillar="SOC", data_type=Indicator.DataType.BOOLEAN)
        self.framework = RegulatoryFramework.objects.create(code="SEL-FW", name="Selector Framework", jurisdiction="INTERNATIONAL")
        OrganizationFramework.objects.create(organization=self.org, framework=self.framework, is_enabled=True)
        
        # Create framework requirements
        req1 = FrameworkRequirement.objects.create(
            framework=self.framework, code="REQ1", title="Requirement 1", pillar="ENV", is_mandatory=True
        )
        req2 = FrameworkRequirement.objects.create(
            framework=self.framework, code="REQ2", title="Requirement 2", pillar="SOC", is_mandatory=False
        )
        
        # Map indicators to requirements
        IndicatorFrameworkMapping.objects.create(
            framework=self.framework, requirement=req1, indicator=self.ind1,
            is_active=True, is_primary=True, mapping_type="primary"
        )
        IndicatorFrameworkMapping.objects.create(
            framework=self.framework, requirement=req2, indicator=self.ind2,
            is_active=True, is_primary=True, mapping_type="primary"
        )
        
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
