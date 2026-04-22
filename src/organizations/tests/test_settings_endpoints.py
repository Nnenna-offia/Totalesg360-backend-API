from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from accounts.models.user import User
from organizations.models import Membership, Organization, OrganizationSettings
from roles.models import Capability, Role, RoleCapability


class OrganizationSettingsEndpointTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.organization = Organization.objects.create(name="Settings Org", sector="manufacturing", country="NG")
        self.user = User.objects.create_user(
            username="settings-admin",
            email="settings@example.com",
            password="password123",
        )

        capability, _ = Capability.objects.get_or_create(
            code="org.manage",
            defaults={"name": "Manage Organization"},
        )
        role = Role.objects.create(code="settings_admin", name="Settings Admin")
        RoleCapability.objects.create(role=role, capability=capability, is_active=True)
        Membership.objects.create(user=self.user, organization=self.organization, role=role, is_active=True)

        self.client.force_authenticate(self.user)
        self.client.credentials(HTTP_X_ORG_ID=str(self.organization.id))

    def test_patch_general_settings_endpoint_updates_preferences(self):
        response = self.client.patch(
            reverse("organizations:settings-general"),
            {
                "system_language": "en",
                "timezone": "Africa/Lagos",
                "currency": "NGN",
                "date_format": "DD/MM/YYYY",
                "admin_theme": "light",
                "notifications_enabled": True,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        settings = OrganizationSettings.objects.get(organization=self.organization)
        self.assertEqual(settings.timezone, "Africa/Lagos")
        self.assertEqual(settings.currency, "NGN")

    def test_patch_security_settings_endpoint_updates_security_flags(self):
        response = self.client.patch(
            reverse("organizations:settings-security"),
            {
                "security_checks_frequency": "daily",
                "require_2fa": True,
                "encrypt_stored_data": True,
                "encryption_method": "AES-256",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        settings = OrganizationSettings.objects.get(organization=self.organization)
        self.assertTrue(settings.require_2fa)
        self.assertTrue(settings.encrypt_stored_data)
        self.assertEqual(settings.encryption_method, "AES-256")