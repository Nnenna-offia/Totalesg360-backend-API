from django.test import TestCase
from rest_framework.test import APIClient
from django.urls import reverse
from accounts.models.user import User
from organizations.models.organization import Organization
from submissions.models.reporting_period import ReportingPeriod
from activities.models.scope import Scope
from activities.models.activity_type import ActivityType
from emissions.models.emission_factor import EmissionFactor
from submissions.services.activity import submit_activity_value
from emissions.tasks import persist_emission_indicators_for_all_locked, persist_emission_indicators_for_period
from indicators.models import Indicator


class EmissionsTasksAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(email='u2@example.com', username='u2', password='pass')
        self.org = Organization.objects.create(name='Test Org 2', sector='manufacturing', country='NG')
        from roles.models.role import Role
        from organizations.models.membership import Membership
        role = Role.objects.create(code='org_admin2', name='Org Admin')
        Membership.objects.create(user=self.user, organization=self.org, role=role)
        self.period = ReportingPeriod.objects.create(organization=self.org, year=2024)
        self.input_indicator = Indicator.objects.create(
            code='S1-DIESEL-L-TASK',
            name='Diesel consumption task',
            pillar='ENV',
            data_type='number',
            collection_method=Indicator.CollectionMethod.ACTIVITY,
            indicator_type=Indicator.IndicatorType.INPUT,
        )
        self.scope1 = Scope.objects.create(name='Scope 1', code='scope1')
        self.activity = ActivityType.objects.create(
            name='Diesel Combustion',
            unit='liters',
            scope=self.scope1,
            indicator=self.input_indicator,
        )
        EmissionFactor.objects.create(
            activity_type=self.activity,
            indicator=self.input_indicator,
            country=None,
            year=2024,
            factor=2.5,
            factor_value=2.5,
            unit='kgCO2e/liter',
            unit_input='liters',
            unit_output='kgCO2e',
        )
        Indicator.objects.create(code='total_scope1_emissions', name='Total Scope 1', pillar='ENV', data_type='number')

    def test_task_persist_and_api_endpoint(self):
        # submit activity
        submit_activity_value(org=self.org, user=self.user, activity_type_id=str(self.activity.id), reporting_period_id=str(self.period.id), value=100)
        # lock period
        self.period.lock(by_user=self.user)

        # run task for all locked
        persist_emission_indicators_for_all_locked()

        # call indicators emission API
        self.client.force_authenticate(user=self.user)
        url = reverse('indicator-emission-value', args=['total_scope1_emissions'])
        resp = self.client.get(url, {'reporting_period_id': str(self.period.id)})
        self.assertEqual(resp.status_code, 200)
        data = resp.json().get('data')
        self.assertEqual(float(data.get('value')), 250.0)
