from django.test import TestCase
from rest_framework.test import APIClient
from django.urls import reverse
from organizations.models.organization import Organization
from accounts.models.user import User
from roles.models.capability import Capability
from roles.models.role import Role
from roles.models.role_capability import RoleCapability
from organizations.models.membership import Membership
from submissions.models import ReportingPeriod

class ReportingPeriodPaginationTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.org = Organization.objects.create(name='PagOrg', sector='tech', country='US')
        self.user = User.objects.create_user(username='paguser', email='p@example.com', password='pass')
        # give user manage_period capability via role
        cap, _ = Capability.objects.get_or_create(code='manage_period', defaults={'name': 'Manage Period'})
        role = Role.objects.create(code='rp_mgr', name='RP Manager')
        RoleCapability.objects.create(role=role, capability=cap)
        Membership.objects.create(user=self.user, organization=self.org, role=role)
        for y in range(2020, 2023):
            for q in (1, 2):
                ReportingPeriod.objects.create(organization=self.org, year=y, quarter=q)
        self.client.force_authenticate(self.user)
        self.client.credentials(HTTP_X_ORG_ID=str(self.org.id))

    def test_reporting_period_pagination(self):
        url = reverse('periods-list-create') + '?page_size=2'
        resp = self.client.get(url)
        assert resp.status_code == 200
        meta = resp.data.get('meta')
        assert meta is not None
        assert 'count' in meta
        assert meta.get('page_size') == 2 or meta.get('page_size') is None
        data = resp.data.get('data')
        assert isinstance(data, list)
        assert len(data) <= 2
from django.test import TestCase
from rest_framework.test import APIClient
from django.urls import reverse
from organizations.models.organization import Organization
from accounts.models.user import User
from roles.models.capability import Capability
from roles.models.role import Role
from roles.models.role_capability import RoleCapability
from organizations.models.membership import Membership
from submissions.models import ReportingPeriod


class ReportingPeriodPaginationTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.org = Organization.objects.create(name='PagOrg', sector='tech', country='US')
        self.user = User.objects.create_user(username='paguser', email='p@example.com', password='pass')
        # give user manage_period capability via role
        cap, _ = Capability.objects.get_or_create(code='manage_period', defaults={'name': 'Manage Period'})
        role = Role.objects.create(code='rp_mgr', name='RP Manager')
        RoleCapability.objects.create(role=role, capability=cap)
        Membership.objects.create(user=self.user, organization=self.org, role=role)
        for y in range(2020, 2023):
            for q in (1, 2):
                ReportingPeriod.objects.create(organization=self.org, year=y, quarter=q)
        self.client.force_authenticate(self.user)
        self.client.credentials(HTTP_X_ORG_ID=str(self.org.id))

    def test_reporting_period_pagination(self):
        url = reverse('periods-list-create') + '?page_size=2'
        resp = self.client.get(url)
        assert resp.status_code == 200
        meta = resp.data.get('meta')
        assert meta is not None
        assert 'count' in meta
        assert meta.get('page_size') == 2 or meta.get('page_size') is None
        data = resp.data.get('data')
        assert isinstance(data, list)
        assert len(data) <= 2