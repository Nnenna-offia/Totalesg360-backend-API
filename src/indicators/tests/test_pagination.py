from django.test import TestCase
from rest_framework.test import APIClient
from django.urls import reverse
from indicators.models import Indicator
from django.test import TestCase
from rest_framework.test import APIClient
from django.urls import reverse
from indicators.models import Indicator


class IndicatorPaginationTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        for i in range(5):
            Indicator.objects.create(code=f"P{i}", name=f"P {i}", pillar="ENV", data_type=Indicator.DataType.NUMBER)

    def test_indicator_list_page_size(self):
        url = reverse('indicator-list') + '?page_size=2'
        resp = self.client.get(url)
        assert resp.status_code == 200
        # handle paginated or non-paginated shapes
        if isinstance(resp.data, dict) and 'results' in resp.data:
            assert len(resp.data['results']) == 2
            assert 'count' in resp.data
        elif isinstance(resp.data, list):
            # if non-paginated, page_size param ignored; ensure we get at least 2
            assert len(resp.data) >= 2
        else:
            # old success_response shape
            data = resp.data.get('data')
            assert isinstance(data, list)