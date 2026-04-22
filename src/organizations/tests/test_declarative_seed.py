from django.test import TestCase

from compliance.models import FrameworkRequirement, IndicatorFrameworkMapping
from indicators.models import FrameworkIndicator, Indicator
from esg_seed.services.seeder import seed_dataset, seed_framework
from esg_seed_data import FRAMEWORKS
from esg_seed_data.gri_305 import GRI_305
from organizations.models import RegulatoryFramework


class DeclarativeSeedTests(TestCase):
    def test_seed_dataset_creates_framework_requirements_indicators_and_mappings(self):
        framework, _ = seed_framework(FRAMEWORKS[0])
        result = seed_dataset(framework=framework, dataset=GRI_305)

        self.assertEqual(framework.code, "GRI")
        self.assertEqual(result["requirements"], 3)
        self.assertEqual(result["indicators"], 3)
        self.assertEqual(result["mappings"], 3)

        self.assertTrue(
            FrameworkRequirement.objects.filter(framework=framework, code="GRI_305_1").exists()
        )
        self.assertTrue(Indicator.objects.filter(code="SCOPE_1").exists())
        self.assertTrue(
            IndicatorFrameworkMapping.objects.filter(
                framework=framework,
                requirement__code="GRI_305_1",
                indicator__code="SCOPE_1",
            ).exists()
        )
        self.assertTrue(
            FrameworkIndicator.objects.filter(
                framework=framework,
                indicator__code="SCOPE_1",
                is_required=True,
            ).exists()
        )

    def test_seed_framework_sets_system_fields(self):
        framework, _ = seed_framework(FRAMEWORKS[0])
        self.assertEqual(framework.jurisdiction, RegulatoryFramework.Jurisdiction.INTERNATIONAL)
        self.assertTrue(framework.is_system)
        self.assertTrue(framework.is_active)
