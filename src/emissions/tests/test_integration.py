from django.test import TestCase
from accounts.models.user import User
from organizations.models.organization import Organization
from organizations.models.facility import Facility
from submissions.models.reporting_period import ReportingPeriod
from activities.models.scope import Scope
from activities.models.activity_type import ActivityType
from emissions.models.emission_factor import EmissionFactor
from submissions.services.activity import submit_activity_value
from emissions.selectors.queries import get_scope1_emissions
from emissions.services.persist_indicators import persist_emission_indicators
from indicators.models import Indicator
from django_countries.fields import Country


class EmissionsIntegrationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email='u@example.com', username='u', password='pass')
        self.org = Organization.objects.create(name='Test Org', sector='manufacturing', country='NG')
        # create a role and membership so user is a member of the org
        from roles.models.role import Role
        from organizations.models.membership import Membership
        role = Role.objects.create(code='org_admin', name='Org Admin')
        Membership.objects.create(user=self.user, organization=self.org, role=role)
        self.period = ReportingPeriod.objects.create(organization=self.org, year=2024)

        # create scope and activity type
        self.scope1 = Scope.objects.create(name='Scope 1', code='scope1')
        self.activity = ActivityType.objects.create(name='Diesel Combustion', unit='liters', scope=self.scope1)

        # create emission factor
        EmissionFactor.objects.create(activity_type=self.activity, country=None, year=2024, factor=2.68, unit='kgCO2e/liter')

        # create indicators for persistence
        Indicator.objects.create(code='total_scope1_emissions', name='Total Scope 1 Emissions', pillar='ENV', data_type='number')

    def test_activity_submission_creates_calculated_emission_and_persist(self):
        # submit activity
        submit_activity_value(org=self.org, user=self.user, activity_type_id=str(self.activity.id), reporting_period_id=str(self.period.id), value=1000, unit='liters')

        # selector should show scope1 sum
        total = get_scope1_emissions(self.org, self.period)
        self.assertAlmostEqual(float(total), 2680.0, places=3)

        # persist indicators
        persist_emission_indicators(self.org, self.period, by_user=self.user, submit=True)

        # DataSubmission should exist
        ds = Indicator.objects.get(code='total_scope1_emissions')
        from submissions.models import DataSubmission
        sub = DataSubmission.objects.filter(organization=self.org, indicator=ds, reporting_period=self.period).first()
        self.assertIsNotNone(sub)
        self.assertAlmostEqual(sub.value_number, 2680.0, places=3)
