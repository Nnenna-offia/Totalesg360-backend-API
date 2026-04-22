from django.test import TestCase
from django.core.exceptions import ValidationError, PermissionDenied

from accounts.models.user import User
from organizations.models.organization import Organization
from roles.models.capability import Capability
from roles.models.role import Role
from roles.models.role_capability import RoleCapability
from organizations.models.membership import Membership
from indicators.models import Indicator, FrameworkIndicator, OrganizationIndicator
from organizations.models import RegulatoryFramework, OrganizationFramework
from submissions.models import ReportingPeriod, DataSubmission
from submissions.services import submit_indicator_value, finalize_period, approve_submission


class SubmissionServicesTests(TestCase):
    def setUp(self):
        self.org = Organization.objects.create(name="T-Org", sector="manufacturing", country="NG")
        self.user = User.objects.create_user(username="u1", email="u1@example.com", password="pass")

        # role & capability
        self.cap_submit, _ = Capability.objects.get_or_create(code="submit_indicator", defaults={"name": "Submit"})
        self.cap_manage, _ = Capability.objects.get_or_create(code="manage_period", defaults={"name": "Manage Period"})
        self.cap_approve, _ = Capability.objects.get_or_create(code="approve_submission", defaults={"name": "Approve"})

        self.role = Role.objects.create(code="data_mgr", name="Data Manager")
        RoleCapability.objects.create(role=self.role, capability=self.cap_submit)
        RoleCapability.objects.create(role=self.role, capability=self.cap_manage)

        # membership linking user -> org with role
        Membership.objects.create(user=self.user, organization=self.org, role=self.role)

        # indicator and org override
        self.ind = Indicator.objects.create(code="I001", name="Indic", pillar="ENV", data_type=Indicator.DataType.NUMBER)
        self.framework = RegulatoryFramework.objects.create(code="SVC-FW", name="Service Framework", jurisdiction="INTERNATIONAL")
        OrganizationFramework.objects.create(organization=self.org, framework=self.framework, is_enabled=True)
        FrameworkIndicator.objects.create(framework=self.framework, indicator=self.ind, is_required=True, display_order=1)
        OrganizationIndicator.objects.create(organization=self.org, indicator=self.ind, is_active=True)

        # reporting period
        self.period = ReportingPeriod.objects.create(organization=self.org, year=2025)

    def test_submit_indicator_value_creates_submission(self):
        obj, created = submit_indicator_value(org=self.org, user=self.user, indicator_id=str(self.ind.id), reporting_period_id=str(self.period.id), value=42)
        self.assertTrue(created)
        self.assertIsInstance(obj, DataSubmission)
        self.assertEqual(obj.value_number, 42.0)

    def test_finalize_period_missing_required_raises(self):
        # mark indicator required for org
        oi = OrganizationIndicator.objects.get(organization=self.org, indicator=self.ind)
        oi.is_required = True
        oi.save()

        with self.assertRaises(ValidationError):
            finalize_period(org=self.org, user=self.user, reporting_period_id=str(self.period.id))

    def test_approve_submission_requires_capability(self):
        # create a submission
        sub, _ = submit_indicator_value(org=self.org, user=self.user, indicator_id=str(self.ind.id), reporting_period_id=str(self.period.id), value=10)
        # remove approve cap from role (ensure user lacks approve)
        # (no RoleCapability for approve was created)

        with self.assertRaises(PermissionDenied):
            approve_submission(org=self.org, user=self.user, submission_id=str(sub.id))
