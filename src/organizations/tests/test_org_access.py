from django.test import TestCase
from rest_framework.test import APIRequestFactory
from rest_framework.exceptions import ValidationError, NotFound, PermissionDenied

from accounts.models.user import User
from organizations.models.organization import Organization
from organizations.models.membership import Membership
from organizations.services import validate_user_organization, OrgHeaderMissing, OrgNotFound, UserNotInOrg
from common.mixins import OrganizationAccessMixin


class OrganizationAccessTests(TestCase):

    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = User.objects.create_user(email='u@example.com', username='u', password='pass')
        self.org = Organization.objects.create(name='Acme Co')
        from roles.models.role import Role
        self.role = Role.objects.create(code='test_role', name='Test Role')

    def test_missing_header_raises(self):
        req = self.factory.get('/some-path')
        req.user = self.user
        with self.assertRaises(OrgHeaderMissing):
            validate_user_organization(req)

    def test_org_not_found_raises(self):
        req = self.factory.get('/some-path', HTTP_X_ORG_ID='00000000-0000-0000-0000-000000000000')
        req.user = self.user
        with self.assertRaises(OrgNotFound):
            validate_user_organization(req)

    def test_user_not_in_org_raises(self):
        req = self.factory.get('/some-path', HTTP_X_ORG_ID=str(self.org.id))
        req.user = self.user
        with self.assertRaises(UserNotInOrg):
            validate_user_organization(req)

    def test_validate_user_organization_success(self):
        # create active membership
        Membership.objects.create(user=self.user, organization=self.org, role=self.role)
        req = self.factory.get('/some-path', HTTP_X_ORG_ID=str(self.org.id))
        req.user = self.user
        org = validate_user_organization(req)
        self.assertIsNotNone(org)
        self.assertEqual(org.id, self.org.id)

    def test_mixin_attaches_org(self):
        # create active membership
        Membership.objects.create(user=self.user, organization=self.org, role=self.role)
        req = self.factory.get('/some-path', HTTP_X_ORG_ID=str(self.org.id))
        req.user = self.user

        class DummyView(OrganizationAccessMixin):
            def __init__(self):
                # mimic APIView initial signature
                pass

        dv = DummyView()
        # call mixin initial implementation
        dv.initial(req)
        self.assertTrue(hasattr(req, 'organization'))
        self.assertEqual(req.organization.id, self.org.id)
