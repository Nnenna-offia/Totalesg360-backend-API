from django.test import TestCase

from organizations.models import Organization, OrganizationESGSettings
from organizations.services.esg_settings import get_active_reporting_period
from submissions.models import ReportingPeriod


class OrganizationESGSettingsTests(TestCase):
    def setUp(self):
        self.organization = Organization.objects.create(
            name="ESG Org",
            sector="manufacturing",
            country="NG",
            entity_type=Organization.EntityType.GROUP,
        )

    def test_esg_settings_created_on_organization_creation(self):
        settings = OrganizationESGSettings.objects.get(organization=self.organization)
        self.assertEqual(settings.reporting_level, Organization.EntityType.GROUP)
        self.assertEqual(settings.reporting_frequency, ReportingPeriod.PeriodType.MONTHLY)

    def test_active_reporting_period_auto_created(self):
        period = get_active_reporting_period(self.organization)

        self.assertIsNotNone(period)
        self.assertEqual(period.organization, self.organization)
        self.assertEqual(period.period_type, ReportingPeriod.PeriodType.MONTHLY)
        self.assertTrue(period.is_active)

    def test_frequency_change_creates_matching_active_period(self):
        settings = self.organization.esg_settings
        settings.reporting_frequency = ReportingPeriod.PeriodType.QUARTERLY
        settings.save(update_fields=["reporting_frequency"])

        period = get_active_reporting_period(self.organization)
        self.assertEqual(period.period_type, ReportingPeriod.PeriodType.QUARTERLY)
