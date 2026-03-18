from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from organizations.models import Organization, Facility
from organizations.models.membership import Membership
from django.contrib.auth import get_user_model
from roles.models import Role, Capability, RoleCapability

User = get_user_model()


class DashboardAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.org = Organization.objects.create(name='Test Org')
        self.user = User.objects.create_user(username='test@example.com', email='test@example.com', password='pass')
        cap, _ = Capability.objects.get_or_create(code='dashboard.view')
        role = Role.objects.create(name='tester', code='tester')
        RoleCapability.objects.create(role=role, capability=cap)
        Membership.objects.create(user=self.user, organization=self.org, role=role, is_active=True)

    def test_summary_unauthenticated(self):
        url = reverse('dashboard-summary')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 401)

    def test_summary_authenticated(self):
        self.client.force_authenticate(user=self.user)
        url = reverse('dashboard-summary')
        resp = self.client.get(url, HTTP_X_ORG_ID=str(self.org.id))
        self.assertEqual(resp.status_code, 200)
