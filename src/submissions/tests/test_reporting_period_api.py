from django.test import TestCase
from rest_framework.test import APIClient
from django.urls import reverse

from accounts.models.user import User
from organizations.models.organization import Organization
from roles.models.capability import Capability
from roles.models.role import Role
from roles.models.role_capability import RoleCapability
from organizations.models.membership import Membership
from submissions.models import ReportingPeriod


class ReportingPeriodAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.org = Organization.objects.create(name="RP-Org", sector="services", country="US")
        self.user = User.objects.create_user(username="user2", email="u2@example.com", password="pass")

        # role & capability
        self.cap_manage, _ = Capability.objects.get_or_create(code="manage_period", defaults={"name": "Manage"})
        self.role = Role.objects.create(code="mgr", name="Manager")
        RoleCapability.objects.create(role=self.role, capability=self.cap_manage)
        Membership.objects.create(user=self.user, organization=self.org, role=self.role)

        self.client.force_authenticate(self.user)
        self.client.credentials(HTTP_X_ORG_ID=str(self.org.id))

    def test_list_periods_empty(self):
        url = reverse('periods-list-create')
        resp = self.client.get(url)
        assert resp.status_code == 200
        assert resp.data.get('data') == []

    def test_create_period_requires_capability(self):
        url = reverse('periods-list-create')
        payload = {"year": 2026, "quarter": 1}
        resp = self.client.post(url, payload, format='json')
        # user has manage_period capability via role -> should be allowed
        if resp.status_code != 201:
            raise AssertionError(f"Unexpected status {resp.status_code}, body={resp.data}")
        data = resp.data.get('data')
        assert data and data.get('year') == 2026
