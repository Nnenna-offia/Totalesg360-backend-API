from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from organizations.models import Organization, OrganizationProfile, BusinessUnit
from roles.models.capability import Capability


class OrganizationProfileAPITest(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username='test', email='t@example.com', password='pass')
        self.org = Organization.objects.create(name='ACME')
        # membership and role setup omitted; mark user as staff for bypass
        self.user.is_staff = True
        self.user.save()
        self.client = Client()
        # login via session for test convenience
        self.client.login(username='test', password='pass')

    def test_patch_profile_json(self):
        url = reverse('organizations:settings-profile')
        resp = self.client.patch(url, data={'registered_business_name': 'ACME Ltd'}, content_type='application/json', **{'HTTP_X-ORG-ID': str(self.org.id)})
        self.assertIn(resp.status_code, (200, 201))
        self.org.refresh_from_db()
        self.assertTrue(hasattr(self.org, 'profile'))
        self.assertEqual(self.org.profile.registered_business_name, 'ACME Ltd')


class BusinessUnitAPITest(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username='test2', email='t2@example.com', password='pass')
        self.user.is_staff = True
        self.user.save()
        self.org = Organization.objects.create(name='ACME2')
        self.client = Client()
        self.client.login(username='test2', password='pass')

    def test_create_list_business_unit(self):
        url = reverse('organizations:business-units')
        resp = self.client.post(url, data={'name': 'Unit A'}, content_type='application/json', **{'HTTP_X-ORG-ID': str(self.org.id)})
        self.assertEqual(resp.status_code, 201)
        resp2 = self.client.get(url, **{'HTTP_X-ORG-ID': str(self.org.id)})
        self.assertEqual(resp2.status_code, 200)
        self.assertTrue(len(resp2.json().get('data')) >= 1)
*** End Patch