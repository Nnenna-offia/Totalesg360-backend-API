from django.test import TestCase
from rest_framework.test import APIClient
from django.urls import reverse

from accounts.models.user import User
from indicators.models import Indicator


class IndicatorAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        # create a normal user and an admin user
        self.user = User.objects.create_user(username="user1", email="u1@example.com", password="pass")
        self.admin = User.objects.create_user(username="admin", email="admin@example.com", password="pass", is_staff=True)

    def test_list_indicators_public(self):
        Indicator.objects.create(code="T1", name="Test 1", pillar="ENV", data_type=Indicator.DataType.NUMBER)
        url = reverse('indicator-list')
        # unauthenticated list should work (ModelViewSet default allows listing if not restricted by code)
        resp = self.client.get(url)
        assert resp.status_code == 200
        # DRF may return paginated structure or raw list depending on settings
        if isinstance(resp.data, list):
            items = resp.data
        elif isinstance(resp.data, dict) and 'results' in resp.data:
            items = resp.data['results']
        else:
            items = resp.data.get('data') if isinstance(resp.data, dict) else None
        assert isinstance(items, (list, type(None)))

    def test_create_requires_admin(self):
        url = reverse('indicator-list')
        payload = {"code": "NEW1", "name": "New", "pillar": "ENV", "data_type": "number"}
        # non-admin should be forbidden
        self.client.force_authenticate(self.user)
        resp = self.client.post(url, payload, format='json')
        assert resp.status_code in (401, 403)
        # admin can create
        self.client.force_authenticate(self.admin)
        resp2 = self.client.post(url, payload, format='json')
        assert resp2.status_code == 201
        assert resp2.data.get('code') == 'NEW1'

    def test_update_delete_require_admin(self):
        ind = Indicator.objects.create(code="UPD1", name="Updatable", pillar="ENV", data_type=Indicator.DataType.NUMBER)
        url = reverse('indicator-detail', kwargs={'pk': str(ind.id)})

        # non-admin cannot update
        self.client.force_authenticate(self.user)
        resp = self.client.patch(url, {"name": "NewName"}, format='json')
        assert resp.status_code in (401, 403)

        # admin can update
        self.client.force_authenticate(self.admin)
        resp2 = self.client.patch(url, {"name": "NewName"}, format='json')
        assert resp2.status_code == 200
        assert resp2.data.get('name') == 'NewName'

        # non-admin cannot delete
        self.client.force_authenticate(self.user)
        resp3 = self.client.delete(url)
        assert resp3.status_code in (401, 403)

        # admin can delete
        self.client.force_authenticate(self.admin)
        resp4 = self.client.delete(url)
        assert resp4.status_code == 204
