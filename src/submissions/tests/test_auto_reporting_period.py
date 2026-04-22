from django.contrib.auth import get_user_model
from django.test import TestCase

from indicators.models import FrameworkIndicator, Indicator
from organizations.models import Membership, Organization, OrganizationFramework, RegulatoryFramework
from roles.models import Capability, Role, RoleCapability
from submissions.services.core import submit_indicator_value


User = get_user_model()


class AutoReportingPeriodSubmissionTests(TestCase):
    def setUp(self):
        self.org = Organization.objects.create(name="Auto Period Org", sector="manufacturing", country="NG")
        self.user = User.objects.create_user(username="auto-period", email="auto@example.com", password="password123")

        role = Role.objects.create(code="submitter", name="Submitter")
        capability = Capability.objects.create(code="submit_indicator", name="Submit Indicator")
        RoleCapability.objects.create(role=role, capability=capability, is_active=True)
        Membership.objects.create(user=self.user, organization=self.org, role=role, is_active=True)

        self.indicator = Indicator.objects.create(
            code="ENV-001",
            name="Energy Use",
            pillar="ENV",
            data_type=Indicator.DataType.NUMBER,
            collection_method=Indicator.CollectionMethod.DIRECT,
        )
        self.framework = RegulatoryFramework.objects.create(code="AUTO-FW", name="Auto Framework", jurisdiction="INTERNATIONAL")
        OrganizationFramework.objects.create(organization=self.org, framework=self.framework, is_enabled=True)
        FrameworkIndicator.objects.create(framework=self.framework, indicator=self.indicator, is_required=True, display_order=1)

    def test_submit_indicator_value_uses_active_reporting_period_when_none_provided(self):
        submission, created = submit_indicator_value(
            org=self.org,
            user=self.user,
            indicator_id=str(self.indicator.id),
            value=42,
        )

        self.assertTrue(created)
        self.assertIsNotNone(submission.reporting_period)
        self.assertTrue(submission.reporting_period.is_active)