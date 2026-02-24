from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model

from organizations.models import Organization, Membership
from roles.models import Role

from common.middleware import OrganizationContextMiddleware


class OrganizationContextMiddlewareTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        User = get_user_model()
        self.user = User.objects.create_user(username='tester', email='tester@example.com', password='pass')
        # Create organization and role
        self.org = Organization.objects.create(name='TestOrg', sector='finance', country='NG')
        self.role = Role.objects.create(code='member', name='Member')
        # Create membership linking user->org
        self.membership = Membership.objects.create(user=self.user, organization=self.org, role=self.role)
        self.middleware = OrganizationContextMiddleware(get_response=lambda r: None)

    def test_header_resolves_org_and_membership(self):
        req = self.factory.get('/')
        req.user = self.user
        # simulate header
        req.META['HTTP_X_ORG_ID'] = str(self.org.id)
        self.middleware.process_request(req)

        self.assertIsNotNone(getattr(req, 'organization', None))
        self.assertEqual(str(req.organization.id), str(self.org.id))
        self.assertIsNotNone(getattr(req, 'membership', None))
        self.assertEqual(req.membership.role.code, 'member')

    def test_user_primary_membership_used_when_no_header(self):
        req = self.factory.get('/')
        req.user = self.user
        # no header
        self.middleware.process_request(req)

        self.assertIsNotNone(req.organization)
        self.assertEqual(req.organization.id, self.org.id)
        self.assertIsNotNone(req.membership)

    def test_header_with_non_member_org_sets_org_but_no_membership(self):
        other = Organization.objects.create(name='OtherOrg', sector='manufacturing', country='NG')
        req = self.factory.get('/')
        req.user = self.user
        req.META['HTTP_X_ORG_ID'] = str(other.id)
        self.middleware.process_request(req)

        self.assertIsNotNone(req.organization)
        self.assertEqual(req.organization.id, other.id)
        self.assertIsNone(req.membership)
