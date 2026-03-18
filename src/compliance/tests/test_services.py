from django.test import TestCase

from organizations.models import Organization, RegulatoryFramework
from indicators.models import Indicator, FrameworkIndicator
from submissions.models import ReportingPeriod, DataSubmission

from compliance.services import compute_framework_completion, compute_organization_compliance, facility_rollup


class ComplianceServicesTests(TestCase):
    def setUp(self):
        self.org = Organization.objects.create(name='E2E Org', sector='manufacturing', country='NG')
        self.framework = RegulatoryFramework.objects.create(code='GRI', name='GRI', jurisdiction='INTERNATIONAL')

        # indicators
        self.ind1 = Indicator.objects.create(code='I1', name='Required 1', pillar='ENV', data_type='number')
        self.ind2 = Indicator.objects.create(code='I2', name='Required 2', pillar='ENV', data_type='number')
        self.ind3 = Indicator.objects.create(code='I3', name='Optional 1', pillar='ENV', data_type='number')

        FrameworkIndicator.objects.create(framework=self.framework, indicator=self.ind1, is_required=True)
        FrameworkIndicator.objects.create(framework=self.framework, indicator=self.ind2, is_required=True)
        FrameworkIndicator.objects.create(framework=self.framework, indicator=self.ind3, is_required=False)

        # assign framework to org
        from organizations.models import OrganizationFramework
        OrganizationFramework.objects.create(organization=self.org, framework=self.framework, is_enabled=True)

        self.period = ReportingPeriod.objects.create(organization=self.org, year=2025)
        from organizations.models import Facility
        self.fac1 = Facility.objects.create(organization=self.org, name='Fac 1')
        self.fac2 = Facility.objects.create(organization=self.org, name='Fac 2')

    def test_framework_completion_and_missing(self):
        # submit one required indicator
        DataSubmission.objects.create(organization=self.org, indicator=self.ind1, reporting_period=self.period, value_number=10.0)
        res = compute_framework_completion(self.org, self.framework, self.period)
        self.assertEqual(res['required_indicators'], 2)
        self.assertEqual(res['submitted_required'], 1)
        self.assertEqual(res['completion_percent'], 50)
        self.assertEqual(res['optional_completed'], 0)

    def test_optional_and_facility_rollup(self):
        # submit optional and required, on different facilities
        DataSubmission.objects.create(organization=self.org, indicator=self.ind1, reporting_period=self.period, value_number=1.0, facility=self.fac1)
        DataSubmission.objects.create(organization=self.org, indicator=self.ind3, reporting_period=self.period, value_number=2.0, facility=self.fac1)
        DataSubmission.objects.create(organization=self.org, indicator=self.ind2, reporting_period=self.period, value_number=3.0, facility=self.fac2)

        org_res = compute_organization_compliance(self.org, self.period)
        self.assertIn('frameworks', org_res)
        # overall_completion: 2 required submitted of 2 -> 100
        self.assertEqual(org_res['overall_completion'], 100)

        rollup = facility_rollup(self.org, self.framework, self.period)
        # two facilities present (ids should match created Facility ids)
        self.assertTrue(any(r['facility_id'] == str(self.fac1.id) or r['facility_id'] == self.fac1.id for r in rollup))
