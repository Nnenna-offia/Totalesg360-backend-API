from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework import generics
from django.conf import settings

from common.permissions import IsOrgMember, HasCapability
from common.api import success_response, problem_response

from targets.models import TargetGoal, TargetMilestone
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError
from indicators.models import Indicator
from organizations.models import Facility
from targets.selectors.target_selectors import get_goals_for_organization, get_goal_milestones
from targets.services.target_progress_service import calculate_target_progress
from .serializers import TargetGoalCreateSerializer, TargetGoalPatchSerializer, MilestoneCreateSerializer


class GoalCreateView(APIView):
    permission_classes = [IsOrgMember, HasCapability]
    required_capability = 'target.create'

    def post(self, request):
        org = getattr(request, 'organization', None)
        data = request.data
        serializer = TargetGoalCreateSerializer(data=data)
        if not serializer.is_valid():
            return problem_response({'type': f"{settings.PROBLEM_BASE_URL}/invalid-request", 'title': 'Invalid payload', 'detail': serializer.errors}, status.HTTP_400_BAD_REQUEST)
        data = serializer.validated_data
        if not org:
            return problem_response({
                'type': f"{settings.PROBLEM_BASE_URL}/invalid-request", 
                'title': 'Organization required', 
                'detail': 'organization header required'}, 
                status.HTTP_400_BAD_REQUEST
                )

        # minimal create; rely on higher-level validation in future
        goal = TargetGoal.objects.create(
            organization=org,
            indicator_id=data.get('indicator_id'),
            facility_id=data.get('facility_id'),
            department_id=data.get('department_id'),
            name=data.get('name', 'Untitled'),
            description=data.get('description', ''),
            reporting_frequency=data.get('reporting_frequency'),
            baseline_year=data.get('baseline_year'),
            baseline_value=data.get('baseline_value'),
            target_year=data.get('target_year'),
            target_value=data.get('target_value'),
            direction=data.get('direction', TargetGoal.Direction.DECREASE),
            created_by=request.user if getattr(request, 'user', None) and request.user.is_authenticated else None,
        )
        return success_response({'goal_id': str(goal.id)}, None, status.HTTP_201_CREATED)


class GoalListView(APIView):
    permission_classes = [IsOrgMember, HasCapability]
    # view and create handled on this endpoint: GET => view, POST => create
    def get_permissions(self):
        if getattr(self, 'request', None) and self.request.method == 'POST':
            self.required_capability = 'target.create'
        else:
            self.required_capability = 'target.view'
        return [IsOrgMember(), HasCapability()]

    def get(self, request):
        org = getattr(request, 'organization', None)
        if not org:
            return problem_response({'type': f"{settings.PROBLEM_BASE_URL}/invalid-request", 'title': 'Organization required', 'detail': 'organization header required'}, status.HTTP_400_BAD_REQUEST)
        goals = get_goals_for_organization(org)
        data = []
        for g in goals:
            data.append({
                'id': str(g.id), 'name': g.name, 'indicator': getattr(g.indicator, 'code', None), 'status': g.status
            })
        return success_response({'goals': data})

    def post(self, request):
        org = getattr(request, 'organization', None)
        data = request.data
        serializer = TargetGoalCreateSerializer(data=data)
        if not serializer.is_valid():
            return problem_response({'type': f"{settings.PROBLEM_BASE_URL}/invalid-request", 'title': 'Invalid payload', 'detail': serializer.errors}, status.HTTP_400_BAD_REQUEST)
        data = serializer.validated_data
        if not org:
            return problem_response({
                'type': f"{settings.PROBLEM_BASE_URL}/invalid-request",
                'title': 'Organization required',
                'detail': 'organization header required'},
                status.HTTP_400_BAD_REQUEST
                )

        # validate referenced indicator
        indicator_id = data.get('indicator_id')
        if not Indicator.objects.filter(id=indicator_id).exists():
            return problem_response({'type': f"{settings.PROBLEM_BASE_URL}/invalid-request", 'title': 'Invalid indicator', 'detail': 'indicator not found'}, status.HTTP_400_BAD_REQUEST)

        # validate facility if provided
        facility_id = data.get('facility_id')
        if facility_id is not None and facility_id != '' and not Facility.objects.filter(id=facility_id).exists():
            return problem_response({'type': f"{settings.PROBLEM_BASE_URL}/invalid-request", 'title': 'Invalid facility', 'detail': 'facility not found'}, status.HTTP_400_BAD_REQUEST)

        try:
            goal = TargetGoal.objects.create(
                organization=org,
                indicator_id=indicator_id,
                facility_id=facility_id,
                name=data.get('name', 'Untitled'),
                description=data.get('description', ''),
                reporting_frequency=data.get('reporting_frequency'),
                baseline_year=data.get('baseline_year'),
                baseline_value=data.get('baseline_value'),
                target_year=data.get('target_year'),
                target_value=data.get('target_value'),
                direction=data.get('direction', TargetGoal.Direction.DECREASE),
                created_by=request.user if getattr(request, 'user', None) and request.user.is_authenticated else None,
            )
        except (DjangoValidationError, IntegrityError) as exc:
            return problem_response({'type': f"{settings.PROBLEM_BASE_URL}/invalid-request", 'title': 'Invalid payload', 'detail': str(exc)}, status.HTTP_400_BAD_REQUEST)
        except Exception:
            import logging
            logging.exception('Unexpected error creating TargetGoal for org %s', getattr(org, 'id', None))
            return problem_response({'type': f"{settings.PROBLEM_BASE_URL}/internal-server-error", 'title': 'Internal Server Error', 'detail': 'An unexpected error occurred.'}, status.HTTP_500_INTERNAL_SERVER_ERROR)

        return success_response({'goal_id': str(goal.id)}, None, status.HTTP_201_CREATED)


class GoalDetailView(APIView):
    permission_classes = [IsOrgMember, HasCapability]

    def get_permissions(self):
        if getattr(self, 'request', None) and self.request.method == 'PATCH':
            self.required_capability = 'target.edit'
        else:
            self.required_capability = 'target.view'
        return [IsOrgMember(), HasCapability()]

    def get(self, request, goal_id):
        org = getattr(request, 'organization', None)
        if not org:
            return problem_response({'type': f"{settings.PROBLEM_BASE_URL}/invalid-request", 'title': 'Organization required', 'detail': 'organization header required'}, status.HTTP_400_BAD_REQUEST)
        goal = TargetGoal.objects.filter(id=goal_id, organization=org).first()
        if not goal:
            return problem_response({'type': f"{settings.PROBLEM_BASE_URL}/not-found", 'title': 'Goal not found', 'detail': 'goal not found'}, status.HTTP_404_NOT_FOUND)
        milestones = get_goal_milestones(goal)
        ms = [{'year': m.year, 'target_value': m.target_value, 'status': m.status} for m in milestones]
        return success_response({'goal': {'id': str(goal.id), 'name': goal.name, 'indicator': getattr(goal.indicator, 'code', None), 'milestones': ms}})

    def patch(self, request, goal_id):
        org = getattr(request, 'organization', None)
        data = request.data
        serializer = TargetGoalPatchSerializer(data=data)
        if not serializer.is_valid():
            return problem_response({'type': f"{settings.PROBLEM_BASE_URL}/invalid-request", 'title': 'Invalid payload', 'detail': serializer.errors}, status.HTTP_400_BAD_REQUEST)
        data = serializer.validated_data
        goal = TargetGoal.objects.filter(id=goal_id, organization=org).first()
        if not goal:
            return problem_response({'type': f"{settings.PROBLEM_BASE_URL}/not-found", 'title': 'Goal not found', 'detail': 'goal not found'}, status.HTTP_404_NOT_FOUND)
        # apply allowed updates
        for fld in ('name', 'description', 'reporting_frequency', 'baseline_year', 'baseline_value', 'target_year', 'target_value', 'direction', 'status'):
            if fld in data:
                setattr(goal, fld, data.get(fld))
        goal.save()
        return success_response({'goal_id': str(goal.id)})





class MilestoneCreateView(APIView):
    permission_classes = [IsOrgMember, HasCapability]
    required_capability = 'target.edit'

    def post(self, request):
        org = getattr(request, 'organization', None)
        data = request.data
        serializer = MilestoneCreateSerializer(data=data)
        if not serializer.is_valid():
            return problem_response({'type': f"{settings.PROBLEM_BASE_URL}/invalid-request", 'title': 'Invalid payload', 'detail': serializer.errors}, status.HTTP_400_BAD_REQUEST)
        data = serializer.validated_data
        if not org:
            return problem_response({'type': f"{settings.PROBLEM_BASE_URL}/invalid-request", 'title': 'Organization required', 'detail': 'organization header required'}, status.HTTP_400_BAD_REQUEST)
        # validate goal exists and belongs to org
        goal_id = data.get('goal_id')
        goal = TargetGoal.objects.filter(id=goal_id, organization=org).first()
        if not goal:
            return problem_response({'type': f"{settings.PROBLEM_BASE_URL}/not-found", 'title': 'Goal not found', 'detail': 'goal not found'}, status.HTTP_404_NOT_FOUND)

        try:
            milestone = TargetMilestone.objects.create(goal=goal, year=data.get('year'), target_value=data.get('target_value'))
        except (DjangoValidationError, IntegrityError) as exc:
            return problem_response({'type': f"{settings.PROBLEM_BASE_URL}/invalid-request", 'title': 'Invalid payload', 'detail': str(exc)}, status.HTTP_400_BAD_REQUEST)
        except Exception:
            import logging
            logging.exception('Unexpected error creating TargetMilestone for org %s', getattr(org, 'id', None))
            return problem_response({'type': f"{settings.PROBLEM_BASE_URL}/internal-server-error", 'title': 'Internal Server Error', 'detail': 'An unexpected error occurred.'}, status.HTTP_500_INTERNAL_SERVER_ERROR)

        return success_response({'milestone_id': str(milestone.id)}, None, status.HTTP_201_CREATED)


class MilestoneListView(APIView):
    permission_classes = [IsOrgMember, HasCapability]
    # GET => view, POST => create (handled here)
    def get_permissions(self):
        if getattr(self, 'request', None) and self.request.method == 'POST':
            self.required_capability = 'target.edit'
        else:
            self.required_capability = 'target.view'
        return [IsOrgMember(), HasCapability()]

    def get(self, request):
        org = getattr(request, 'organization', None)
        if not org:
            return problem_response({'type': f"{settings.PROBLEM_BASE_URL}/invalid-request", 'title': 'Organization required', 'detail': 'organization header required'}, status.HTTP_400_BAD_REQUEST)
        # list milestones for org's goals
        goals = TargetGoal.objects.filter(organization=org).values_list('id', flat=True)
        mqs = TargetMilestone.objects.filter(goal_id__in=goals)
        data = [{'id': str(m.id), 'goal_id': str(m.goal_id), 'year': m.year, 'target_value': m.target_value, 'status': m.status} for m in mqs]
        return success_response({'milestones': data})

    def post(self, request):
        org = getattr(request, 'organization', None)
        data = request.data
        serializer = MilestoneCreateSerializer(data=data)
        if not serializer.is_valid():
            return problem_response({'type': f"{settings.PROBLEM_BASE_URL}/invalid-request", 'title': 'Invalid payload', 'detail': serializer.errors}, status.HTTP_400_BAD_REQUEST)
        data = serializer.validated_data
        if not org:
            return problem_response({'type': f"{settings.PROBLEM_BASE_URL}/invalid-request", 'title': 'Organization required', 'detail': 'organization header required'}, status.HTTP_400_BAD_REQUEST)
        # validate goal exists and belongs to org
        goal_id = data.get('goal_id')
        goal = TargetGoal.objects.filter(id=goal_id, organization=org).first()
        if not goal:
            return problem_response({'type': f"{settings.PROBLEM_BASE_URL}/not-found", 'title': 'Goal not found', 'detail': 'goal not found'}, status.HTTP_404_NOT_FOUND)

        try:
            milestone = TargetMilestone.objects.create(goal=goal, year=data.get('year'), target_value=data.get('target_value'))
        except (DjangoValidationError, IntegrityError) as exc:
            return problem_response({'type': f"{settings.PROBLEM_BASE_URL}/invalid-request", 'title': 'Invalid payload', 'detail': str(exc)}, status.HTTP_400_BAD_REQUEST)
        except Exception:
            import logging
            logging.exception('Unexpected error creating TargetMilestone for org %s', getattr(org, 'id', None))
            return problem_response({'type': f"{settings.PROBLEM_BASE_URL}/internal-server-error", 'title': 'Internal Server Error', 'detail': 'An unexpected error occurred.'}, status.HTTP_500_INTERNAL_SERVER_ERROR)

        return success_response({'milestone_id': str(milestone.id)}, None, status.HTTP_201_CREATED)


class ProgressView(APIView):
    permission_classes = [IsOrgMember, HasCapability]
    required_capability = 'target.view'

    def get(self, request, goal_id):
        org = getattr(request, 'organization', None)
        if not org:
            return problem_response({'type': f"{settings.PROBLEM_BASE_URL}/invalid-request", 'title': 'Organization required', 'detail': 'organization header required'}, status.HTTP_400_BAD_REQUEST)
        goal = TargetGoal.objects.filter(id=goal_id, organization=org).first()
        if not goal:
            return problem_response({'type': f"{settings.PROBLEM_BASE_URL}/not-found", 'title': 'Goal not found', 'detail': 'goal not found'}, status.HTTP_404_NOT_FOUND)
        res = calculate_target_progress(goal)
        return success_response({'progress': res})
