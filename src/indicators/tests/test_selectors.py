from django.test import TestCase

from indicators.models import Indicator, OrganizationIndicator
from compliance.models import FrameworkRequirement, IndicatorFrameworkMapping
from organizations.models import RegulatoryFramework, Organization, OrganizationFramework
from indicators.selectors.queries import get_active_indicators, get_framework_indicators, get_org_effective_indicators


class IndicatorSelectorsTest(TestCase):
    def setUp(self):
        # Indicators
        self.ind_a = Indicator.objects.create(code="IND_A", name="Indicator A", pillar="ENV", data_type="number")
        self.ind_b = Indicator.objects.create(code="IND_B", name="Indicator B", pillar="SOC", data_type="percent")
        self.ind_c = Indicator.objects.create(code="IND_C", name="Indicator C", pillar="GOV", data_type="number")

        # Frameworks
        self.fw1 = RegulatoryFramework.objects.create(code="FW1", name="Framework 1", jurisdiction="INTERNATIONAL")
        self.fw2 = RegulatoryFramework.objects.create(code="FW2", name="Framework 2", jurisdiction="INTERNATIONAL")

        # Framework mappings: fw1 requires ind_a, fw1 optional ind_b; fw2 requires ind_b
        fw1_req_required = FrameworkRequirement.objects.create(
            framework=self.fw1, code="FW1_REQ_A", title="FW1 Required A", pillar="ENV", is_mandatory=True, priority=1
        )
        fw1_req_optional = FrameworkRequirement.objects.create(
            framework=self.fw1, code="FW1_REQ_B", title="FW1 Optional B", pillar="SOC", is_mandatory=False, priority=2
        )
        fw2_req_required_b = FrameworkRequirement.objects.create(
            framework=self.fw2, code="FW2_REQ_B", title="FW2 Required B", pillar="SOC", is_mandatory=True, priority=1
        )
        fw2_req_required_c = FrameworkRequirement.objects.create(
            framework=self.fw2, code="FW2_REQ_C", title="FW2 Required C", pillar="GOV", is_mandatory=True, priority=2
        )
        IndicatorFrameworkMapping.objects.create(framework=self.fw1, requirement=fw1_req_required, indicator=self.ind_a, is_active=True, is_primary=True, mapping_type="primary")
        IndicatorFrameworkMapping.objects.create(framework=self.fw1, requirement=fw1_req_optional, indicator=self.ind_b, is_active=True, is_primary=True, mapping_type="primary")
        IndicatorFrameworkMapping.objects.create(framework=self.fw2, requirement=fw2_req_required_b, indicator=self.ind_b, is_active=True, is_primary=True, mapping_type="primary")
        IndicatorFrameworkMapping.objects.create(framework=self.fw2, requirement=fw2_req_required_c, indicator=self.ind_c, is_active=True, is_primary=True, mapping_type="primary")

        # Organization
        self.org = Organization.objects.create(name="Org X", sector="manufacturing", country="NG")

        # Assign fw1 enabled, fw2 disabled initially
        OrganizationFramework.objects.create(organization=self.org, framework=self.fw1, is_enabled=True)
        OrganizationFramework.objects.create(organization=self.org, framework=self.fw2, is_enabled=False)

    def test_get_framework_indicators_ordering(self):
        qs = get_framework_indicators(self.fw1)
        codes = [mapping.indicator.code for mapping in qs]
        self.assertEqual(codes, ["IND_A", "IND_B"])  # requirement priority 1 then 2

    def test_get_org_effective_indicators_framework_requirement(self):
        qs = get_org_effective_indicators(self.org).order_by('code')
        data = {r.code: r for r in qs}

        # ind_a is required by fw1 (enabled) -> effective required True
        self.assertTrue(data["IND_A"].required_by_framework)
        self.assertTrue(data["IND_A"].is_required_effective)

        # ind_b is not required by enabled frameworks (fw2 is disabled) -> effective required False
        self.assertFalse(data["IND_B"].required_by_framework)
        self.assertFalse(data["IND_B"].is_required_effective)

        # defaults: is_active_effective should be True
        self.assertTrue(data["IND_A"].is_active_effective)
        self.assertTrue(data["IND_B"].is_active_effective)

    def test_org_overrides_take_precedence(self):
        # Add an organization-level override for IND_B: required True, active False
        OrganizationIndicator.objects.create(organization=self.org, indicator=self.ind_b, is_required=True, is_active=False)

        # Enable fw2 so it would also require IND_B at framework level
        ofw2 = OrganizationFramework.objects.get(organization=self.org, framework=self.fw2)
        ofw2.is_enabled = True
        ofw2.save()

        qs = get_org_effective_indicators(self.org).order_by('code')
        data = {r.code: r for r in qs}

        # IND_B should be marked as overridden and reflect the org override values
        self.assertTrue(data["IND_B"].overridden)
        self.assertTrue(data["IND_B"].is_required_effective)  # override True
        self.assertFalse(data["IND_B"].is_active_effective)  # override False

    def test_get_active_indicators_requires_active_framework_and_enabled_pillar(self):
        active_codes = list(get_active_indicators(self.org).order_by('code').values_list('code', flat=True))
        self.assertEqual(active_codes, ["IND_A", "IND_B"])

        settings = self.org.esg_settings
        settings.enable_social = False
        settings.save(update_fields=['enable_social'])

        filtered_codes = list(get_active_indicators(self.org).order_by('code').values_list('code', flat=True))
        self.assertEqual(filtered_codes, ["IND_A"])

        org_framework = OrganizationFramework.objects.get(organization=self.org, framework=self.fw2)
        org_framework.is_enabled = True
        org_framework.save(update_fields=['is_enabled'])
        settings.enable_social = True
        settings.save(update_fields=['enable_social'])

        all_codes = list(get_active_indicators(self.org).order_by('code').values_list('code', flat=True))
        self.assertEqual(all_codes, ["IND_A", "IND_B", "IND_C"])
