"""Seed ESG framework, requirement, indicator, and mapping data from declarative datasets."""
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from esg_seed.services.seeder import seed_dataset, seed_framework
from esg_seed_data import FRAMEWORKS, FRAMEWORK_DATASETS


class Command(BaseCommand):
    help = "Seed ESG declarative data (frameworks, requirements, indicators, mappings)"

    def handle(self, *args, **options):
        self.stdout.write("Seeding ESG data from declarative datasets...")
        summary = self._seed_all()
        self.stdout.write(
            self.style.SUCCESS(
                "Seeding complete: "
                f"frameworks={summary['frameworks']}, "
                f"requirements={summary['requirements']}, "
                f"indicators={summary['indicators']}, "
                f"mappings={summary['mappings']}"
            )
        )

    @transaction.atomic
    def _seed_all(self):
        framework_map = {}
        total_frameworks = 0
        total_requirements = 0
        total_indicators = 0
        total_mappings = 0

        for framework_data in FRAMEWORKS:
            framework, created = seed_framework(framework_data)
            framework_map[framework_data["code"]] = framework
            total_frameworks += 1
            status = "Created" if created else "Upserted"
            self.stdout.write(f"  {status} framework: {framework.code}")

        for dataset in FRAMEWORK_DATASETS:
            framework_code = dataset.get("framework")
            framework = framework_map.get(framework_code)
            if framework is None:
                raise CommandError(
                    f"Dataset references unknown framework code '{framework_code}'. "
                    "Define it in esg_seed_data/frameworks.py"
                )

            result = seed_dataset(framework=framework, dataset=dataset)
            total_requirements += result["requirements"]
            total_indicators += result["indicators"]
            total_mappings += result["mappings"]
            self.stdout.write(
                "  Seeded dataset for "
                f"{framework.code}: requirements={result['requirements']}, "
                f"indicators={result['indicators']}, mappings={result['mappings']}"
            )

        return {
            "frameworks": total_frameworks,
            "requirements": total_requirements,
            "indicators": total_indicators,
            "mappings": total_mappings,
        }
