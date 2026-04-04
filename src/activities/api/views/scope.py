from rest_framework.views import APIView
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from common.api import success_response, problem_response
from common.permissions import HasCapability
from accounts.selectors.org_context import get_org_and_membership
from activities.models.scope import Scope
from ..serializers import ScopeSerializer
from django.conf import settings


class ScopeListCreateAPIView(APIView):
	permission_classes = [IsAuthenticated]
	
	def get(self, request):
		"""List all scopes."""
		queryset = Scope.objects.all().order_by('code')
		serializer = ScopeSerializer(queryset, many=True)
		return success_response(data=serializer.data)
	
	def post(self, request):
		"""
		Create a new scope.
		Requires 'manage_activity_types' capability.
		"""
		org, membership = get_org_and_membership(request=request)
		
		from types import SimpleNamespace
		temp_view = SimpleNamespace(required_capability='manage_activity_types')
		if not HasCapability().has_permission(request, temp_view):
			return problem_response({
				'type': f"{settings.PROBLEM_BASE_URL}/forbidden",
				'title': 'Forbidden',
				'detail': "You don't have permission to manage scopes"

			}, status.HTTP_403_FORBIDDEN)
		
		serializer = ScopeSerializer(data=request.data)
		serializer.is_valid(raise_exception=True)
		scope = serializer.save()
		
		return success_response(data=serializer.data, status=status.HTTP_201_CREATED)


class ScopeDetailAPIView(APIView):
	permission_classes = [IsAuthenticated]
	
	def get_object(self, pk):
		try:
			return Scope.objects.get(pk=pk)
		except Scope.DoesNotExist:
			return None
	
	def get(self, request, pk):
		"""Get scope details."""
		scope = self.get_object(pk)
		if not scope:
			return problem_response({
				'type': f"{settings.PROBLEM_BASE_URL}/not_found",
				'title': 'Not Found',
				'detail': 'Scope not found'
			}, status=status.HTTP_404_NOT_FOUND)
		
		serializer = ScopeSerializer(scope)
		return success_response(data=serializer.data)
	
	def patch(self, request, pk):
		"""
		Update a scope.
		Requires 'manage_activity_types' capability.
		"""
		org, membership = get_org_and_membership(request=request)
		
		from types import SimpleNamespace
		temp_view = SimpleNamespace(required_capability='manage_activity_types')
		if not HasCapability().has_permission(request, temp_view):
			return problem_response({
				'type': f"{settings.PROBLEM_BASE_URL}/forbidden",
				'title': 'Forbidden',
				'detail': "You don't have permission to manage scopes"
			}, status=status.HTTP_403_FORBIDDEN)
		
		scope = self.get_object(pk)
		if not scope:
			return problem_response({
				'type': f"{settings.PROBLEM_BASE_URL}/not_found",
				'title': 'Not Found',
				'detail': 'Scope not found'
			}, status=status.HTTP_404_NOT_FOUND)
		
		serializer = ScopeSerializer(scope, data=request.data, partial=True)
		serializer.is_valid(raise_exception=True)
		scope = serializer.save()
		
		return success_response(data=serializer.data)
	
	def delete(self, request, pk):
		"""
		Delete a scope.
		Requires 'manage_activity_types' capability.
		Only allowed if no activity types reference it.
		"""
		org, membership = get_org_and_membership(request=request)
		
		from types import SimpleNamespace
		temp_view = SimpleNamespace(required_capability='manage_activity_types')
		if not HasCapability().has_permission(request, temp_view):
			return problem_response({
				'type': f"{settings.PROBLEM_BASE_URL}/forbidden",
				'title': 'Forbidden',
				'detail': "You don't have permission to manage scopes"
			}, status=status.HTTP_403_FORBIDDEN)
		
		scope = self.get_object(pk)
		if not scope:
			return problem_response({
				'type': f"{settings.PROBLEM_BASE_URL}/not_found",
				'title': 'Not Found',
				'detail': 'Scope not found'
			}, status=status.HTTP_404_NOT_FOUND)
		
		# Check if any activity types reference this scope
		activity_type_count = scope.activity_types.count()
		if activity_type_count > 0:
			return problem_response({
				'type': f"{settings.PROBLEM_BASE_URL}/bad_request",
				'title': 'Bad Request',
				'detail': f"Cannot delete scope with {activity_type_count} activity types"
			}, status=status.HTTP_400_BAD_REQUEST)
		
		scope.delete()
		return success_response(
			message="Scope deleted successfully",
			status=status.HTTP_204_NO_CONTENT
		)
