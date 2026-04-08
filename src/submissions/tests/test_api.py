from django.test import TestCase
from rest_framework.test import APIClient
from django.urls import reverse

from accounts.models.user import User
from organizations.models.organization import Organization
from roles.models.capability import Capability
from roles.models.role import Role
from roles.models.role_capability import RoleCapability
from organizations.models.membership import Membership
from indicators.models import Indicator, OrganizationIndicator
from submissions.models import ReportingPeriod, DataSubmission


class SubmissionsAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.org = Organization.objects.create(name="T-Org-API", sector="manufacturing", country="NG")
        self.user = User.objects.create_user(username="apiuser", email="api@example.com", password="pass")

        # capabilities and role
        self.cap_submit, _ = Capability.objects.get_or_create(code="submit_indicator", defaults={"name": "Submit"})
        self.cap_manage, _ = Capability.objects.get_or_create(code="manage_period", defaults={"name": "Manage Period"})
        self.cap_approve, _ = Capability.objects.get_or_create(code="approve_submission", defaults={"name": "Approve"})

        self.role = Role.objects.create(code="data_mgr", name="Data Manager")
        RoleCapability.objects.create(role=self.role, capability=self.cap_submit)
        RoleCapability.objects.create(role=self.role, capability=self.cap_manage)

        Membership.objects.create(user=self.user, organization=self.org, role=self.role)

        self.ind = Indicator.objects.create(code="API001", name="API Indic", pillar="ENV", data_type=Indicator.DataType.NUMBER)
        OrganizationIndicator.objects.create(organization=self.org, indicator=self.ind, is_active=True)

        self.period = ReportingPeriod.objects.create(organization=self.org, year=2025)

        # authenticate and set org header for requests
        self.client.force_authenticate(self.user)
        self.client.credentials(HTTP_X_ORG_ID=str(self.org.id))

    def test_submit_endpoint_creates_submission(self):
        url = reverse('submit-indicator')
        payload = {
            "indicator_id": str(self.ind.id),
            "reporting_period_id": str(self.period.id),
            "value": 12,
        }
        resp = self.client.post(url, payload, format='json')
        assert resp.status_code in (200, 201)
        data = resp.data.get('data')
        assert data and data.get('value_number') == 12.0

    def test_period_list_returns_submissions(self):
        # create a submission via service to ensure it's present
        DataSubmission.objects.create(organization=self.org, indicator=self.ind, reporting_period=self.period, value_number=5.0)
        url = reverse('period-submissions', kwargs={'period_id': str(self.period.id)})
        resp = self.client.get(url)
        assert resp.status_code == 200
        items = resp.data.get('data')
        assert isinstance(items, list) and len(items) >= 1

    def test_finalize_requires_manage_capability(self):
        # mark indicator required so finalize will fail due to missing submissions
        oi = OrganizationIndicator.objects.get(organization=self.org, indicator=self.ind)
        oi.is_required = True
        oi.save()

        url = reverse('finalize-period', kwargs={'period_id': str(self.period.id)})
        resp = self.client.post(url, {}, format='json')
        # missing required indicator submissions should return 400/problem
        assert resp.status_code == 400

    def test_approve_requires_capability(self):
        # create submission
        sub = DataSubmission.objects.create(organization=self.org, indicator=self.ind, reporting_period=self.period, value_number=1.0)
        url = reverse('approve-submission', kwargs={'submission_id': str(sub.id)})
        resp = self.client.post(url, {}, format='json')
        # user lacks approve capability -> 403
        assert resp.status_code == 403
