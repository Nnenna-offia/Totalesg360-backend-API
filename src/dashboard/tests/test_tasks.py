from django.test import TestCase
from django.utils import timezone

from accounts.models import User
from organizations.models import Organization
from roles.models import Role, Capability, RoleCapability
from organizations.models.membership import Membership

from dashboard.tasks import populate_dashboard_snapshots
from dashboard.models import DashboardSnapshot, EmissionSnapshot, IndicatorSnapshot, TargetSnapshot, ComplianceSnapshot


class DashboardTasksTest(TestCase):
    def setUp(self):
        # create an org and a user with membership so selectors have context
        self.org = Organization.objects.create(name='SnapOrg')
        self.user = User.objects.create_user(username='snapper', email='snapper@example.com', password='pass')
        role = Role.objects.create(name='tester', code='tester')
        cap, _ = Capability.objects.get_or_create(code='dashboard.view')
        RoleCapability.objects.create(role=role, capability=cap)
        Membership.objects.create(user=self.user, organization=self.org, role=role, is_active=True)

    def test_populate_dashboard_snapshots_creates_records(self):
        # Run task synchronously (Celery is eager in tests via settings)
        res = populate_dashboard_snapshots()
        # Ensure snapshots exist for the org
        self.assertTrue(DashboardSnapshot.objects.filter(organization=self.org).exists())
        self.assertTrue(EmissionSnapshot.objects.filter(organization=self.org).exists())
        self.assertTrue(IndicatorSnapshot.objects.filter(organization=self.org).exists())
        self.assertTrue(TargetSnapshot.objects.filter(organization=self.org).exists())
        self.assertTrue(ComplianceSnapshot.objects.filter(organization=self.org).exists())
