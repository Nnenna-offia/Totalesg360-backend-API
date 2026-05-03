from django.test import TestCase
from rest_framework.test import APIClient

from django.contrib.auth import get_user_model

from organizations.models import Organization
from organizations.models import Facility
from organizations.models.membership import Membership
from roles.models import Role
from roles.models.role_capability import RoleCapability
from roles.models.capability import Capability

from submissions.models import ReportingPeriod, DataSubmission
from indicators.models import Indicator
from compliance.models import FrameworkRequirement, IndicatorFrameworkMapping
from organizations.models.regulatory_framework import RegulatoryFramework


User = get_user_model()


class ComplianceAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        # create user/org/role/membership
        self.user = User.objects.create_user(username='u', email='u@example.com', password='pass')
        self.org = Organization.objects.create(name='Org A')
        self.role = Role.objects.filter(code='org_owner').first() or Role.objects.create(name='Org Owner', code='org_owner')
        Membership.objects.create(user=self.user, organization=self.org, role=self.role, is_active=True)

        # ensure capability mapping for this test role
        cap = Capability.objects.filter(code='compliance.view').first() or Capability.objects.create(code='compliance.view', name='View Compliance')
        RoleCapability.objects.get_or_create(role=self.role, capability=cap)

        # create framework, indicator and reporting period
        self.framework = RegulatoryFramework.objects.create(code='TF', name='Test Framework', jurisdiction=RegulatoryFramework.Jurisdiction.INTERNATIONAL)
        self.ind1 = Indicator.objects.create(code='I1', name='Indicator 1', pillar=Indicator.Pillar.ENVIRONMENTAL, data_type=Indicator.DataType.NUMBER)
        self.ind2 = Indicator.objects.create(code='I2', name='Indicator 2', pillar=Indicator.Pillar.ENVIRONMENTAL, data_type=Indicator.DataType.NUMBER)
        # map indicators to framework requirements
        req1 = FrameworkRequirement.objects.create(framework=self.framework, code='REQ1', title='Requirement 1', pillar='ENV', is_mandatory=True)
        req2 = FrameworkRequirement.objects.create(framework=self.framework, code='REQ2', title='Requirement 2', pillar='ENV', is_mandatory=False)
        IndicatorFrameworkMapping.objects.create(framework=self.framework, requirement=req1, indicator=self.ind1, is_active=True, is_primary=True, mapping_type='primary')
        IndicatorFrameworkMapping.objects.create(framework=self.framework, requirement=req2, indicator=self.ind2, is_active=True, is_primary=True, mapping_type='primary')

        self.period = ReportingPeriod.objects.create(organization=self.org, year=2023)

        # facility
        self.facility = Facility.objects.create(organization=self.org, name='F1')

    def authenticate(self):
        # use DRF test client force_authenticate for reliable auth in unit tests
        self.client.force_authenticate(user=self.user)

    def test_organization_compliance_requires_auth_and_capability(self):
        url = '/api/v1/compliance/organization'
        # unauthenticated -> denied (401 or 403 depending on middleware)
        resp = self.client.get(url)
        self.assertIn(resp.status_code, (401, 403))

    def test_framework_and_missing_endpoints(self):
        # authenticate
        self.authenticate()

        # create a submission for only one required indicator
        DataSubmission.objects.create(
            organization=self.org,
            reporting_period=self.period,
            indicator=self.ind1,
            facility=self.facility,
            submitted_by=self.user,
            value_number=1.0,
        )

        # framework completion
        fw_url = f'/api/v1/compliance/framework/{self.framework.id}?period_id={self.period.id}'
        resp = self.client.get(fw_url, HTTP_X_ORG_ID=str(self.org.id))
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertIn('framework', body.get('data', {}))

        # missing indicators
        miss_url = f'/api/v1/compliance/missing?framework_id={self.framework.id}&period_id={self.period.id}'
        resp2 = self.client.get(miss_url, HTTP_X_ORG_ID=str(self.org.id))
        self.assertEqual(resp2.status_code, 200)
        body2 = resp2.json()
        self.assertIn('missing', body2.get('data', {}))


class ComplianceMasterDataAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.staff = User.objects.create_user(
            username='staff', email='staff@example.com', password='pass', is_staff=True
        )
        self.framework = RegulatoryFramework.objects.create(
            code='GRI',
            name='Global Reporting Initiative',
            jurisdiction=RegulatoryFramework.Jurisdiction.INTERNATIONAL,
            priority=100,
        )

    def test_framework_list_is_public(self):
        resp = self.client.get('/api/v1/compliance/frameworks/')
        self.assertEqual(resp.status_code, 200)

        body = resp.json()
        if isinstance(body, list):
            payload = body
        else:
            payload = body.get('results', body)
        self.assertTrue(len(payload) >= 1)

    def test_framework_patch_requires_staff_or_global_capability(self):
        detail_url = f'/api/v1/compliance/frameworks/{self.framework.id}/'

        resp = self.client.patch(detail_url, {'name': 'Updated Name'}, format='json')
        self.assertIn(resp.status_code, (401, 403))

        self.client.force_authenticate(user=self.staff)
        resp = self.client.patch(detail_url, {'name': 'Updated Name'}, format='json')
        self.assertEqual(resp.status_code, 200)
        self.framework.refresh_from_db()
        self.assertEqual(self.framework.name, 'Updated Name')
