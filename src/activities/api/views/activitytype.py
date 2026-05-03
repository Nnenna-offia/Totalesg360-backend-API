from rest_framework.views import APIView
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.db.models import Count, Q

from common.api import success_response, problem_response
from common.permissions import HasGlobalCapability, IsOrgMember
from activities.models.activity_type import ActivityType
from ..serializers import (
	ActivityTypeListSerializer, 
	ActivityTypeDetailSerializer, 
	ActivityTypeCreateUpdateSerializer
)
from django.conf import settings
from accounts.selectors.org_context import get_org_and_membership
from indicators.selectors.queries import get_active_indicators

class ActivityTypeListCreateAPIView(APIView):
	required_capability = 'manage_activity_types'

	def get_permissions(self):
		if self.request.method in ('GET', 'HEAD', 'OPTIONS'):
			return [AllowAny()]
		return [IsAuthenticated(), HasGlobalCapability()]
	
	def get(self, request):
		"""
		List all activity types.
		Query params:
		- scope: Filter by scope code
		- is_active: Filter by active status (true/false)
		- has_indicator: Filter by whether linked to indicator (true/false)
		- search: Search in name and description
		"""
		# Don't require org context for listing catalog
		queryset = ActivityType.objects.select_related('scope', 'indicator').all()
		
		# Filters
		scope_code = request.query_params.get('scope')
		if scope_code:
			queryset = queryset.filter(scope__code=scope_code)
		
		# category filtering removed: grouping is handled by Indicator -> ActivityType
		
		is_active = request.query_params.get('is_active')
		if is_active is not None:
			is_active_bool = is_active.lower() == 'true'
			queryset = queryset.filter(is_active=is_active_bool)
		
		has_indicator = request.query_params.get('has_indicator')
		if has_indicator is not None:
			has_indicator_bool = has_indicator.lower() == 'true'
			if has_indicator_bool:
				queryset = queryset.filter(indicator__isnull=False)
			else:
				queryset = queryset.filter(indicator__isnull=True)
		
		search = request.query_params.get('search')
		if search:
			queryset = queryset.filter(
				Q(name__icontains=search) | Q(description__icontains=search)
			)
		
		queryset = queryset.order_by('-created_at')
		serializer = ActivityTypeListSerializer(queryset, many=True)
		return success_response(data=serializer.data)
	
	def post(self, request):
		"""
		Create a new activity type.
		Requires 'manage_activity_types' capability.
		"""
		serializer = ActivityTypeCreateUpdateSerializer(data=request.data)
		serializer.is_valid(raise_exception=True)
		
		activity_type = serializer.save()
		
		out_serializer = ActivityTypeDetailSerializer(activity_type)
		return success_response(data=out_serializer.data, status=status.HTTP_201_CREATED)


class ActivityTypeDetailAPIView(APIView):
	required_capability = 'manage_activity_types'

	def get_permissions(self):
		if self.request.method in ('GET', 'HEAD', 'OPTIONS'):
			return [AllowAny()]
		return [IsAuthenticated(), HasGlobalCapability()]
	
	def get_object(self, pk):
		try:
			return ActivityType.objects.select_related('scope', 'indicator').get(pk=pk)
		except ActivityType.DoesNotExist:
			return None
	
	def get(self, request, pk):
		"""Get detailed activity type information."""
		activity_type = self.get_object(pk)
		if not activity_type:
			return problem_response({
				'type': f"{settings.PROBLEM_BASE_URL}/not_found",
				'title': 'Not Found',
				'detail': 'Activity type not found'
			}, status.HTTP_404_NOT_FOUND)
		
		serializer = ActivityTypeDetailSerializer(activity_type)
		return success_response(data=serializer.data)
	
	def patch(self, request, pk):
		"""
		Update an activity type.
		Requires 'manage_activity_types' capability.
		"""
		activity_type = self.get_object(pk)
		if not activity_type:
			return problem_response({
				'type': f"{settings.PROBLEM_BASE_URL}/not_found",
				'title': 'Not Found',
				'detail': 'Activity type not found'
			}, status.HTTP_404_NOT_FOUND)
		
		serializer = ActivityTypeCreateUpdateSerializer(
			activity_type, 
			data=request.data, 
			partial=True
		)
		serializer.is_valid(raise_exception=True)
		activity_type = serializer.save()
		
		out_serializer = ActivityTypeDetailSerializer(activity_type)
		return success_response(data=out_serializer.data)
	
	def delete(self, request, pk):
		"""
		Delete an activity type.
		Requires 'manage_activity_types' capability.
		Only allowed if no submissions exist.
		"""
		
		activity_type = self.get_object(pk)
		if not activity_type:
			return problem_response({
				'type': f"{settings.PROBLEM_BASE_URL}/not_found",
				'title': 'Not Found',
				'detail': 'Activity type not found'
			}, status.HTTP_404_NOT_FOUND)
		
		# Check if any submissions exist
		submission_count = activity_type.submissions.count()
		if submission_count > 0:
			return problem_response({
				'type': f"{settings.PROBLEM_BASE_URL}/bad_request",
				'title': 'Invalid Request',
				'detail': f"Cannot delete activity type with {submission_count} existing submissions. Consider deactivating instead."
			}, status.HTTP_400_BAD_REQUEST)
		
		activity_type.delete()
		return success_response(data={"message": "Activity type deleted successfully"}, status=status.HTTP_204_NO_CONTENT)


class OrgActiveActivityTypesView(APIView):
	"""
	Return activity types whose linked indicator is active for the requesting org.
	Requires X-ORG-ID header (or authenticated user must have a primary org membership).
	Mirrors GET /api/v1/indicators/active/.
	"""
	permission_classes = [IsAuthenticated, IsOrgMember]

	def get(self, request):
		org, _ = get_org_and_membership(request=request)
		active_indicators = get_active_indicators(org)
		queryset = (
			ActivityType.objects
			.filter(indicator__in=active_indicators, is_active=True)
			.select_related('scope', 'indicator')
			.order_by('indicator__pillar', 'name')
		)
		serializer = ActivityTypeListSerializer(queryset, many=True)
		return success_response(data={'activity_types': serializer.data})
