from django.test import TestCase

from indicators.models import Indicator, OrganizationIndicator
from compliance.models import FrameworkRequirement, IndicatorFrameworkMapping
from organizations.models import RegulatoryFramework, Organization, OrganizationFramework
from indicators.services import sync_org_indicators_for_org


class IndicatorServicesTest(TestCase):
    def setUp(self):
        # Indicators
        self.ind_a = Indicator.objects.create(code="SVC_A", name="Svc A", pillar="ENV", data_type="number")
        self.ind_b = Indicator.objects.create(code="SVC_B", name="Svc B", pillar="SOC", data_type="percent")

        # Frameworks
        self.fw1 = RegulatoryFramework.objects.create(code="SFW1", name="Svc Framework 1", jurisdiction="INTERNATIONAL")
        self.fw2 = RegulatoryFramework.objects.create(code="SFW2", name="Svc Framework 2", jurisdiction="INTERNATIONAL")

        # Framework mappings: fw1 requires ind_a; fw2 requires ind_b
        fw1_req = FrameworkRequirement.objects.create(
            framework=self.fw1, code="SFW1_REQ_A", title="SFW1 Required A", pillar="ENV", is_mandatory=True
        )
        fw2_req = FrameworkRequirement.objects.create(
            framework=self.fw2, code="SFW2_REQ_B", title="SFW2 Required B", pillar="SOC", is_mandatory=True
        )
        IndicatorFrameworkMapping.objects.create(framework=self.fw1, requirement=fw1_req, indicator=self.ind_a, is_active=True, is_primary=True, mapping_type="primary")
        IndicatorFrameworkMapping.objects.create(framework=self.fw2, requirement=fw2_req, indicator=self.ind_b, is_active=True, is_primary=True, mapping_type="primary")

        # Organization
        self.org = Organization.objects.create(name="SvcOrg", sector="finance", country="NG")

    def test_sync_creates_org_indicators(self):
        # Enable fw1 and fw2 for org
        OrganizationFramework.objects.create(organization=self.org, framework=self.fw1, is_enabled=True)
        OrganizationFramework.objects.create(organization=self.org, framework=self.fw2, is_enabled=True)

        created, updated, skipped = sync_org_indicators_for_org(self.org)
        self.assertEqual(created, 2)
        self.assertEqual(updated, 0)
        self.assertEqual(skipped, 0)

        # Verify OrganizationIndicator rows exist
        oi_a = OrganizationIndicator.objects.get(organization=self.org, indicator=self.ind_a)
        oi_b = OrganizationIndicator.objects.get(organization=self.org, indicator=self.ind_b)

        self.assertIsNone(oi_a.is_required)
        self.assertTrue(oi_a.is_active)
        self.assertIsNone(oi_b.is_required)
        self.assertTrue(oi_b.is_active)

    def test_sync_skips_overridden_and_updates_inactive(self):
        # Enable fw1 and fw2
        OrganizationFramework.objects.create(organization=self.org, framework=self.fw1, is_enabled=True)
        OrganizationFramework.objects.create(organization=self.org, framework=self.fw2, is_enabled=True)

        # Pre-create override for ind_b where org explicitly sets is_required=True
        OrganizationIndicator.objects.create(organization=self.org, indicator=self.ind_b, is_required=True, is_active=True)

        # Pre-create inactive OrganizationIndicator for ind_a with is_required=None
        OrganizationIndicator.objects.create(organization=self.org, indicator=self.ind_a, is_required=None, is_active=False)

        created, updated, skipped = sync_org_indicators_for_org(self.org)

        # ind_b: skipped because it has explicit is_required != None
        # ind_a: updated (reactivated)
        self.assertEqual(created, 0)
        self.assertEqual(updated, 1)
        self.assertEqual(skipped, 1)

        oi_a = OrganizationIndicator.objects.get(organization=self.org, indicator=self.ind_a)
        oi_b = OrganizationIndicator.objects.get(organization=self.org, indicator=self.ind_b)

        self.assertTrue(oi_a.is_active)
        self.assertTrue(oi_b.is_required)
