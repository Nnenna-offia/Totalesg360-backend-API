from rest_framework import viewsets
from rest_framework.permissions import IsAdminUser, AllowAny
from rest_framework.pagination import PageNumberPagination
from common.permissions import HasGlobalCapability

from indicators.models import Indicator
from .serializers import IndicatorSerializer


class IndicatorViewSet(viewsets.ModelViewSet):
	"""Admin-managed CRUD for global Indicators.

	Read (GET) is public; writes require admin.
	"""
	queryset = Indicator.objects.all().order_by('code')
	serializer_class = IndicatorSerializer
	pagination_class = PageNumberPagination
	required_capability = 'manage_indicators'

	def get_permissions(self):
		# allow anyone to list/retrieve
		if self.request.method in ('GET', 'HEAD', 'OPTIONS'):
			return [AllowAny()]
		# allow staff or global capability holders
		return [HasGlobalCapability()]
