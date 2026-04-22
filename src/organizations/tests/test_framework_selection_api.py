from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from accounts.models.user import User
from organizations.models import Membership, Organization, OrganizationFramework, RegulatoryFramework
from roles.models import Capability, Role, RoleCapability


class OrganizationFrameworkSelectionAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.organization = Organization.objects.create(name="Framework Org", sector="manufacturing", country="NG")
        self.user = User.objects.create_user(username="framework-admin", email="framework@example.com", password="password123")

        capability, _ = Capability.objects.get_or_create(code="org.manage", defaults={"name": "Manage Organization"})
        role = Role.objects.create(code="framework_admin", name="Framework Admin")
        RoleCapability.objects.create(role=role, capability=capability, is_active=True)
        Membership.objects.create(user=self.user, organization=self.organization, role=role, is_active=True)

        self.gri = RegulatoryFramework.objects.create(code="GRI-T", name="GRI Test", jurisdiction="INTERNATIONAL", priority=100)
        self.tcfd = RegulatoryFramework.objects.create(code="TCFD-T", name="TCFD Test", jurisdiction="INTERNATIONAL", priority=90)
        self.custom = RegulatoryFramework.objects.create(code="CUSTOM-T", name="Custom Test", jurisdiction="INTERNATIONAL", is_system=False)

        OrganizationFramework.objects.create(
            organization=self.organization,
            framework=self.gri,
            is_enabled=True,
            is_primary=True,
        )

        self.client.force_authenticate(self.user)
        self.client.credentials(HTTP_X_ORG_ID=str(self.organization.id))

    def test_get_framework_options_includes_assignment_state(self):
        response = self.client.get(reverse('organizations:framework-selection'))

        self.assertEqual(response.status_code, 200)
        payload = response.data['data']['frameworks']
        self.assertEqual([item['code'] for item in payload], ['GRI-T', 'TCFD-T'])

        gri_option = next(item for item in payload if item['code'] == 'GRI-T')
        tcfd_option = next(item for item in payload if item['code'] == 'TCFD-T')

        self.assertTrue(gri_option['is_assigned'])
        self.assertTrue(gri_option['is_active'])
        self.assertTrue(gri_option['is_primary'])
        self.assertFalse(tcfd_option['is_assigned'])
        self.assertFalse(tcfd_option['is_active'])

    def test_patch_framework_selection_updates_assignment_state(self):
        response = self.client.patch(
            reverse('organizations:framework-selection'),
            {
                'frameworks': [
                    {'framework_id': str(self.gri.id), 'is_active': False},
                    {'framework_id': str(self.tcfd.id), 'is_active': True},
                ]
            },
            format='json',
        )

        self.assertEqual(response.status_code, 200)

        self.assertFalse(
            OrganizationFramework.objects.get(organization=self.organization, framework=self.gri).is_enabled
        )

        tcfd_assignment = OrganizationFramework.objects.get(organization=self.organization, framework=self.tcfd)
        self.assertTrue(tcfd_assignment.is_enabled)
        self.assertTrue(tcfd_assignment.is_primary)

    def test_patch_rejects_non_system_framework(self):
        response = self.client.patch(
            reverse('organizations:framework-selection'),
            {
                'frameworks': [
                    {'framework_id': str(self.custom.id), 'is_active': True},
                ]
            },
            format='json',
        )

        self.assertEqual(response.status_code, 400)