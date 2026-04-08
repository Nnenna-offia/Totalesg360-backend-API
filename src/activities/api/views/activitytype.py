from rest_framework.views import APIView
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.db.models import Count, Q

from common.api import success_response, problem_response
from common.mixins import OrganizationAccessMixin
from common.permissions import HasCapability
from accounts.selectors.org_context import get_org_and_membership
from activities.models.activity_type import ActivityType
from ..serializers import (
	ActivityTypeListSerializer, 
	ActivityTypeDetailSerializer, 
	ActivityTypeCreateUpdateSerializer
)
from django.conf import settings

class ActivityTypeListCreateAPIView(OrganizationAccessMixin, APIView):
	permission_classes = [IsAuthenticated]
	
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
		# `OrganizationAccessMixin` ensures `request.organization` exists
		org, membership = get_org_and_membership(request=request)
		
		# Create a temporary view object with required_capability for permission check
		from types import SimpleNamespace
		temp_view = SimpleNamespace(required_capability='activity.edit')
		if not HasCapability().has_permission(request, temp_view):
			return problem_response({
				'type': f"{settings.PROBLEM_BASE_URL}/forbidden",
				'title': 'Forbidden',
				'detail': f"You don't have permission to manage activity types ({temp_view.required_capability})"
			}, status.HTTP_403_FORBIDDEN)
		
		serializer = ActivityTypeCreateUpdateSerializer(data=request.data)
		serializer.is_valid(raise_exception=True)
		
		activity_type = serializer.save()
		
		out_serializer = ActivityTypeDetailSerializer(activity_type)
		return success_response(data=out_serializer.data, status=status.HTTP_201_CREATED)


class ActivityTypeDetailAPIView(APIView):
	permission_classes = [IsAuthenticated]
	
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
		org, membership = get_org_and_membership(request=request)
		
		from types import SimpleNamespace
		temp_view = SimpleNamespace(required_capability='manage_activity_types')
		if not HasCapability().has_permission(request, temp_view):
			return problem_response({
				'type': f"{settings.PROBLEM_BASE_URL}/forbidden",
				'title': 'Forbidden',
				'detail': f"You don't have permission to manage activity types ({temp_view.required_capability})"
			}, status.HTTP_403_FORBIDDEN)
		
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
		
		org, membership = get_org_and_membership(request=request)
		
		from types import SimpleNamespace
		temp_view = SimpleNamespace(required_capability='manage_activity_types')
		if not HasCapability().has_permission(request, temp_view):
			return problem_response({
				'type': f"{settings.PROBLEM_BASE_URL}/forbidden",
				'title': 'Forbidden',
				'detail': "You don't have permission to manage activity types"
			}, status.HTTP_403_FORBIDDEN)
		
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
