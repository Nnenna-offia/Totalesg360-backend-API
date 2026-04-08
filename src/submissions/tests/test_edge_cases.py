from django.test import TestCase
from django.core.exceptions import ValidationError

from accounts.models.user import User
from organizations.models.organization import Organization
from roles.models.capability import Capability
from roles.models.role import Role
from roles.models.role_capability import RoleCapability
from organizations.models.membership import Membership
from indicators.models import Indicator, OrganizationIndicator
from submissions.models import ReportingPeriod, DataSubmission
from submissions.services import submit_indicator_value


class EdgeCaseTests(TestCase):
    def setUp(self):
        self.org = Organization.objects.create(name="EdgeOrg", sector="finance", country="NG")
        self.user = User.objects.create_user(username="edge", email="edge@example.com", password="pass")
        self.role = Role.objects.create(code="r", name="R")
        self.cap, _ = Capability.objects.get_or_create(code="submit_indicator", defaults={"name": "Submit"})
        RoleCapability.objects.create(role=self.role, capability=self.cap)
        Membership.objects.create(user=self.user, organization=self.org, role=self.role)

        self.ind_num = Indicator.objects.create(code="E1", name="Num", pillar="ENV", data_type=Indicator.DataType.NUMBER)
        self.ind_bool = Indicator.objects.create(code="E2", name="Bool", pillar="ENV", data_type=Indicator.DataType.BOOLEAN)
        OrganizationIndicator.objects.create(organization=self.org, indicator=self.ind_num, is_active=True)
        OrganizationIndicator.objects.create(organization=self.org, indicator=self.ind_bool, is_active=True)

        self.period = ReportingPeriod.objects.create(organization=self.org, year=2025)

    def test_submit_invalid_type_raises(self):
        # submit text for numeric indicator
        with self.assertRaises(ValidationError):
            submit_indicator_value(org=self.org, user=self.user, indicator_id=str(self.ind_num.id), reporting_period_id=str(self.period.id), value="not-a-number")

    def test_submit_bool_with_non_bool_raises(self):
        with self.assertRaises(ValidationError):
            submit_indicator_value(org=self.org, user=self.user, indicator_id=str(self.ind_bool.id), reporting_period_id=str(self.period.id), value="true")

    def test_locked_period_rejected(self):
        self.period.status = ReportingPeriod.Status.LOCKED
        self.period.save()
        with self.assertRaises(Exception):
            submit_indicator_value(org=self.org, user=self.user, indicator_id=str(self.ind_num.id), reporting_period_id=str(self.period.id), value=1)
