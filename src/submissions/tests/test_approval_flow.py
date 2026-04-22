from django.test import TestCase
from rest_framework.test import APIClient
from django.urls import reverse

from accounts.models.user import User
from organizations.models.organization import Organization
from roles.models.capability import Capability
from roles.models.role import Role
from roles.models.role_capability import RoleCapability
from organizations.models.membership import Membership
from indicators.models import Indicator, FrameworkIndicator, OrganizationIndicator
from organizations.models import RegulatoryFramework, OrganizationFramework
from submissions.models import ReportingPeriod, DataSubmission


class ApprovalFlowTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.org = Organization.objects.create(name="ApproveOrg", sector="manufacturing", country="NG")

        # submitter user
        self.submit_user = User.objects.create_user(username="submit", email="submit@example.com", password="pass")
        cap_submit, _ = Capability.objects.get_or_create(code="submit_indicator", defaults={"name": "Submit"})
        role_submit = Role.objects.create(code="r_submit", name="Submitter")
        RoleCapability.objects.create(role=role_submit, capability=cap_submit)
        Membership.objects.create(user=self.submit_user, organization=self.org, role=role_submit)

        # approver user
        self.approver = User.objects.create_user(username="approver", email="approver@example.com", password="pass")
        cap_approve, _ = Capability.objects.get_or_create(code="approve_submission", defaults={"name": "Approve"})
        role_approve = Role.objects.create(code="r_approve", name="Approver")
        RoleCapability.objects.create(role=role_approve, capability=cap_approve)
        Membership.objects.create(user=self.approver, organization=self.org, role=role_approve)

        # indicator and period
        self.ind = Indicator.objects.create(code="A1", name="A1", pillar="ENV", data_type=Indicator.DataType.NUMBER)
        self.framework = RegulatoryFramework.objects.create(code="APP-FW", name="Approval Framework", jurisdiction="INTERNATIONAL")
        OrganizationFramework.objects.create(organization=self.org, framework=self.framework, is_enabled=True)
        FrameworkIndicator.objects.create(framework=self.framework, indicator=self.ind, is_required=True, display_order=1)
        OrganizationIndicator.objects.create(organization=self.org, indicator=self.ind, is_active=True)
        self.period = ReportingPeriod.objects.create(organization=self.org, year=2025)

    def test_approver_can_approve_submission(self):
        # create submission by submitter via API
        self.client.force_authenticate(self.submit_user)
        self.client.credentials(HTTP_X_ORG_ID=str(self.org.id))
        submit_url = reverse('submit-indicator')
        payload = {"indicator_id": str(self.ind.id), "value": 7}
        resp = self.client.post(submit_url, payload, format='json')
        assert resp.status_code in (200, 201)
        sub_id = resp.data['data']['id']

        # approver performs approve
        self.client.force_authenticate(self.approver)
        self.client.credentials(HTTP_X_ORG_ID=str(self.org.id))
        approve_url = reverse('approve-submission', kwargs={'submission_id': sub_id})
        resp2 = self.client.post(approve_url, {}, format='json')
        assert resp2.status_code == 200
        data = resp2.data.get('data')
        assert data.get('status') == DataSubmission.Status.APPROVED
        assert data.get('approved_by') is not None
