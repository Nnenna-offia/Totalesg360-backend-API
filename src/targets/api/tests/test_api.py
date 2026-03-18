from django.test import TestCase
from rest_framework.test import APIClient

from django.contrib.auth import get_user_model
from organizations.models import Organization
from roles.models import Role
from roles.models.capability import Capability
from roles.models.role_capability import RoleCapability

from indicators.models import Indicator
from submissions.models import ReportingPeriod, DataSubmission
from targets.models import TargetGoal, TargetMilestone

User = get_user_model()


class TargetsAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='apiu', email='api@example.com', password='pass')
        self.org = Organization.objects.create(name='OrgAPI')
        self.role = Role.objects.filter(code='org_owner').first() or Role.objects.create(name='Org Owner', code='org_owner')
        # ensure membership for user in org with role
        from organizations.models.membership import Membership
        Membership.objects.create(user=self.user, organization=self.org, role=self.role, is_active=True)
        # ensure capability mapping exists on role
        # ensure create/edit/view capabilities present on role for tests
        cap_view, _ = Capability.objects.get_or_create(code='target.view', defaults={'name':'View Targets'})
        cap_create, _ = Capability.objects.get_or_create(code='target.create', defaults={'name':'Create Targets'})
        cap_edit, _ = Capability.objects.get_or_create(code='target.edit', defaults={'name':'Edit Targets'})
        RoleCapability.objects.get_or_create(role=self.role, capability=cap_view)
        RoleCapability.objects.get_or_create(role=self.role, capability=cap_create)
        RoleCapability.objects.get_or_create(role=self.role, capability=cap_edit)

        self.ind = Indicator.objects.create(code='S1', name='Scope 1', pillar=Indicator.Pillar.ENVIRONMENTAL, data_type=Indicator.DataType.NUMBER)

    def auth_headers(self):
        # force auth and org header
        self.client.force_authenticate(user=self.user)
        return {'HTTP_X_ORG_ID': str(self.org.id)}

    def test_create_goal_and_list(self):
        headers = self.auth_headers()
        payload = {
            'indicator_id': str(self.ind.id),
            'name': 'Reduce S1',
            'baseline_year': 2022,
            'baseline_value': 1200.0,
            'target_year': 2030,
            'target_value': 800.0,
            'direction': 'decrease',
        }
        resp = self.client.post('/api/v1/targets/goals/create', data=payload, format='json', **headers)
        self.assertEqual(resp.status_code, 201)

        # list
        resp2 = self.client.get('/api/v1/targets/goals', **headers)
        self.assertEqual(resp2.status_code, 200)
        body = resp2.json()
        self.assertIn('goals', body.get('data', {}))

    def test_milestone_and_progress(self):
        # create goal
        g = TargetGoal.objects.create(organization=self.org, indicator=self.ind, name='G', baseline_year=2022, baseline_value=100.0, target_year=2030, target_value=50.0, direction=TargetGoal.Direction.DECREASE)
        headers = self.auth_headers()
        # create milestone
        payload = {'goal_id': str(g.id), 'year': 2025, 'target_value': 90.0}
        resp = self.client.post('/api/v1/targets/milestones/create', data=payload, format='json', **headers)
        self.assertEqual(resp.status_code, 201)

        # add submission and fetch progress
        period = ReportingPeriod.objects.create(organization=self.org, year=2023)
        DataSubmission.objects.create(organization=self.org, reporting_period=period, indicator=self.ind, value_number=95.0)
        resp2 = self.client.get(f'/api/v1/targets/progress/{g.id}', **headers)
        self.assertEqual(resp2.status_code, 200)
        body = resp2.json()
        self.assertIn('progress', body.get('data', {}))
