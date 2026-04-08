from django.test import TestCase
from django.urls import reverse

from django.contrib.auth import get_user_model

from organizations.models import Organization, Membership
from roles.models import Role, Capability, RoleCapability
from organizations.api.views import OrganizationOptionsView
from common.permissions import IsOrgMember, HasCapability
from rest_framework.permissions import IsAuthenticated


class OrgGuardIntegrationTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username="u1", email="u1@example.com", password="pass")
        self.other = User.objects.create_user(username="u2", email="u2@example.com", password="pass")

        # Create org, role, capability and membership
        self.org = Organization.objects.create(name="ACME", sector="finance", country="NG")
        self.role = Role.objects.create(code="org_admin", name="Org Admin")
        self.cap, _ = Capability.objects.get_or_create(code="org.manage", defaults={"name": "Manage Org"})
        RoleCapability.objects.create(role=self.role, capability=self.cap)

        # Add membership linking self.user -> org with role
        Membership.objects.create(user=self.user, organization=self.org, role=self.role)

        # Patch the existing view to require org membership + capability for this test
        from rest_framework.authentication import SessionAuthentication

        OrganizationOptionsView.authentication_classes = (SessionAuthentication,)
        OrganizationOptionsView.permission_classes = (IsAuthenticated, IsOrgMember, HasCapability)
        OrganizationOptionsView.required_capability = "org.manage"

    def test_allowed_when_member_and_has_capability(self):
        self.client.force_login(self.user)
        url = reverse("organizations:options")
        resp = self.client.get(url, HTTP_X_ORG_ID=str(self.org.id))
        self.assertEqual(resp.status_code, 200)

    def test_denied_when_not_member_or_missing_capability(self):
        # other user not a member
        self.client.force_login(self.other)
        url = reverse("organizations:options")
        resp = self.client.get(url, HTTP_X_ORG_ID=str(self.org.id))
        self.assertIn(resp.status_code, (401, 403))
