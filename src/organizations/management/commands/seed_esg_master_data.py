from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from activities.models import ActivityType, Scope
from compliance.models import FrameworkRequirement, IndicatorFrameworkMapping
from emissions.services.indicator_traceability import INPUT_TO_DERIVED_INDICATOR
from indicators.models import Indicator
from organizations.models import RegulatoryFramework


FRAMEWORKS = [
    {
        "code": "GRI",
        "name": "Global Reporting Initiative",
        "jurisdiction": RegulatoryFramework.Jurisdiction.INTERNATIONAL,
        "description": "Global sustainability reporting standards.",
        "priority": 100,
    },
    {
        "code": "ISSB",
        "name": "ISSB (IFRS S1/S2)",
        "jurisdiction": RegulatoryFramework.Jurisdiction.INTERNATIONAL,
        "description": "IFRS sustainability disclosure standards S1 and S2.",
        "priority": 95,
    },
    {
        "code": "TCFD",
        "name": "Task Force on Climate-related Financial Disclosures",
        "jurisdiction": RegulatoryFramework.Jurisdiction.INTERNATIONAL,
        "description": "Climate-related governance, strategy, risk, and metrics disclosures.",
        "priority": 90,
    },
    {
        "code": "SASB",
        "name": "SASB Standards",
        "jurisdiction": RegulatoryFramework.Jurisdiction.INTERNATIONAL,
        "description": "Industry-specific sustainability accounting metrics.",
        "priority": 85,
    },
    {
        "code": "CDP",
        "name": "Carbon Disclosure Project",
        "jurisdiction": RegulatoryFramework.Jurisdiction.INTERNATIONAL,
        "description": "Climate and emissions disclosure framework.",
        "priority": 80,
    },
    {
        "code": "UN_SDG",
        "name": "UN Sustainable Development Goals",
        "jurisdiction": RegulatoryFramework.Jurisdiction.INTERNATIONAL,
        "description": "UN SDG-aligned sustainability outcome framework.",
        "priority": 70,
    },
    {
        "code": "NESREA",
        "name": "NESREA Environmental Compliance",
        "jurisdiction": RegulatoryFramework.Jurisdiction.NIGERIA,
        "description": "Nigerian environmental standards and regulations.",
        "priority": 88,
    },
    {
        "code": "CBN_ESG",
        "name": "CBN ESG Guidelines",
        "jurisdiction": RegulatoryFramework.Jurisdiction.NIGERIA,
        "description": "Central Bank of Nigeria ESG and risk disclosure guidance.",
        "priority": 86,
    },
    {
        "code": "NSE_ESG",
        "name": "Nigerian Exchange ESG Disclosure",
        "jurisdiction": RegulatoryFramework.Jurisdiction.NIGERIA,
        "description": "NSE/NGX sustainability disclosure expectations.",
        "priority": 84,
    },
    {
        "code": "FMENV",
        "name": "Federal Ministry of Environment Requirements",
        "jurisdiction": RegulatoryFramework.Jurisdiction.NIGERIA,
        "description": "Federal Ministry of Environment regulatory obligations.",
        "priority": 82,
    },
]


REQUIREMENTS = {
    "GRI": [
        {
            "code": "GRI 305-1",
            "title": "Scope 1 emissions",
            "pillar": FrameworkRequirement.Pillar.ENVIRONMENTAL,
            "is_mandatory": True,
        },
        {
            "code": "GRI 305-2",
            "title": "Scope 2 emissions",
            "pillar": FrameworkRequirement.Pillar.ENVIRONMENTAL,
            "is_mandatory": True,
        },
        {
            "code": "GRI 305-3",
            "title": "Scope 3 emissions",
            "pillar": FrameworkRequirement.Pillar.ENVIRONMENTAL,
            "is_mandatory": True,
        },
    ],
    "ISSB": [
        {
            "code": "IFRS S2-1",
            "title": "Gross Scope 1 greenhouse gas emissions",
            "pillar": FrameworkRequirement.Pillar.ENVIRONMENTAL,
            "is_mandatory": True,
        },
        {
            "code": "IFRS S2-2",
            "title": "Gross Scope 2 greenhouse gas emissions",
            "pillar": FrameworkRequirement.Pillar.ENVIRONMENTAL,
            "is_mandatory": True,
        },
        {
            "code": "IFRS S2-3",
            "title": "Gross Scope 3 greenhouse gas emissions",
            "pillar": FrameworkRequirement.Pillar.ENVIRONMENTAL,
            "is_mandatory": True,
        },
    ],
    "TCFD": [
        {
            "code": "TCFD-Metrics-1",
            "title": "Disclose Scope 1, 2, and relevant Scope 3 emissions",
            "pillar": FrameworkRequirement.Pillar.ENVIRONMENTAL,
            "is_mandatory": True,
        }
    ],
    "SASB": [
        {
            "code": "SASB-EM-EP-110a.1",
            "title": "Gross global Scope 1 emissions",
            "pillar": FrameworkRequirement.Pillar.ENVIRONMENTAL,
            "is_mandatory": True,
        },
        {
            "code": "SASB-EM-EP-130a.1",
            "title": "Discussion of emissions reduction strategy",
            "pillar": FrameworkRequirement.Pillar.ENVIRONMENTAL,
            "is_mandatory": False,
        },
    ],
    "CDP": [
        {
            "code": "CDP-C6.1",
            "title": "Gross global Scope 1 emissions",
            "pillar": FrameworkRequirement.Pillar.ENVIRONMENTAL,
            "is_mandatory": True,
        },
        {
            "code": "CDP-C6.3",
            "title": "Gross global Scope 2 emissions",
            "pillar": FrameworkRequirement.Pillar.ENVIRONMENTAL,
            "is_mandatory": True,
        },
    ],
    "UN_SDG": [
        {
            "code": "SDG-13.2",
            "title": "Integrate climate change measures",
            "pillar": FrameworkRequirement.Pillar.ENVIRONMENTAL,
            "is_mandatory": False,
        }
    ],
    "NESREA": [
        {
            "code": "NESREA-AIR-01",
            "title": "Air emission monitoring and disclosure",
            "pillar": FrameworkRequirement.Pillar.ENVIRONMENTAL,
            "is_mandatory": True,
        }
    ],
    "CBN_ESG": [
        {
            "code": "CBN-ENV-01",
            "title": "Environmental risk and emissions reporting",
            "pillar": FrameworkRequirement.Pillar.ENVIRONMENTAL,
            "is_mandatory": True,
        }
    ],
    "NSE_ESG": [
        {
            "code": "NSE-E-01",
            "title": "Energy use and GHG disclosure",
            "pillar": FrameworkRequirement.Pillar.ENVIRONMENTAL,
            "is_mandatory": True,
        }
    ],
    "FMENV": [
        {
            "code": "FMENV-EM-01",
            "title": "Environmental performance and emissions returns",
            "pillar": FrameworkRequirement.Pillar.ENVIRONMENTAL,
            "is_mandatory": True,
        }
    ],
}


INPUT_INDICATORS = [
    {
        "code": "S1-DIESEL-L",
        "name": "Diesel consumption",
        "description": "Diesel fuel consumed for stationary/mobile operations.",
        "pillar": Indicator.Pillar.ENVIRONMENTAL,
        "data_type": Indicator.DataType.NUMBER,
        "unit": "litres",
    },
    {
        "code": "S1-LPG-KG",
        "name": "LPG consumption",
        "description": "Liquefied petroleum gas used in operations.",
        "pillar": Indicator.Pillar.ENVIRONMENTAL,
        "data_type": Indicator.DataType.NUMBER,
        "unit": "kg",
    },
    {
        "code": "S1-NATGAS-M3",
        "name": "Natural gas usage",
        "description": "Natural gas used in process/energy applications.",
        "pillar": Indicator.Pillar.ENVIRONMENTAL,
        "data_type": Indicator.DataType.NUMBER,
        "unit": "m3",
    },
    {
        "code": "S1-REFRIG-KG",
        "name": "Refrigerant leakage",
        "description": "Leakage volume of refrigerants with GHG potential.",
        "pillar": Indicator.Pillar.ENVIRONMENTAL,
        "data_type": Indicator.DataType.NUMBER,
        "unit": "kg",
    },
    {
        "code": "S2-ELEC-KWH",
        "name": "Electricity consumption",
        "description": "Purchased electricity consumed.",
        "pillar": Indicator.Pillar.ENVIRONMENTAL,
        "data_type": Indicator.DataType.NUMBER,
        "unit": "kWh",
    },
    {
        "code": "S3-FERT-KG",
        "name": "Fertilizer usage",
        "description": "Fertilizer quantity used in agricultural operations.",
        "pillar": Indicator.Pillar.ENVIRONMENTAL,
        "data_type": Indicator.DataType.NUMBER,
        "unit": "kg",
    },
    {
        "code": "S3-TRANSPORT-KM",
        "name": "Transport distance",
        "description": "Distance traveled by logistics and distribution operations.",
        "pillar": Indicator.Pillar.ENVIRONMENTAL,
        "data_type": Indicator.DataType.NUMBER,
        "unit": "km",
    },
    {
        "code": "S3-WASTE-M3",
        "name": "Waste volume",
        "description": "Waste generated/disposed volume.",
        "pillar": Indicator.Pillar.ENVIRONMENTAL,
        "data_type": Indicator.DataType.NUMBER,
        "unit": "m3",
    },
    {
        "code": "S3-FEED-KG",
        "name": "Feed consumption (livestock)",
        "description": "Animal feed consumed in livestock operations.",
        "pillar": Indicator.Pillar.ENVIRONMENTAL,
        "data_type": Indicator.DataType.NUMBER,
        "unit": "kg",
    },
]


DERIVED_INDICATORS = [
    {
        "code": "ENV-S1-EMISSIONS-TCO2E",
        "name": "Scope 1 emissions",
        "description": "Derived Scope 1 emissions from direct activity inputs.",
        "pillar": Indicator.Pillar.ENVIRONMENTAL,
        "data_type": Indicator.DataType.NUMBER,
        "unit": "tCO2e",
        "calculation_method": "sum(scope1_activity_values * emission_factors)",
    },
    {
        "code": "ENV-S2-EMISSIONS-TCO2E",
        "name": "Scope 2 emissions",
        "description": "Derived Scope 2 emissions from purchased electricity data.",
        "pillar": Indicator.Pillar.ENVIRONMENTAL,
        "data_type": Indicator.DataType.NUMBER,
        "unit": "tCO2e",
        "calculation_method": "sum(scope2_activity_values * emission_factors)",
    },
    {
        "code": "ENV-S3-EMISSIONS-TCO2E",
        "name": "Scope 3 emissions",
        "description": "Derived Scope 3 emissions from upstream/downstream inputs.",
        "pillar": Indicator.Pillar.ENVIRONMENTAL,
        "data_type": Indicator.DataType.NUMBER,
        "unit": "tCO2e",
        "calculation_method": "sum(scope3_activity_values * emission_factors)",
    },
    {
        "code": "ENV-TOTAL-EMISSIONS-TCO2E",
        "name": "Total emissions",
        "description": "Derived total emissions = Scope 1 + Scope 2 + Scope 3.",
        "pillar": Indicator.Pillar.ENVIRONMENTAL,
        "data_type": Indicator.DataType.NUMBER,
        "unit": "tCO2e",
        "calculation_method": "scope1 + scope2 + scope3",
    },
]


PRIMARY_DERIVED_INDICATOR_MAPPING = {
    "ENV-S1-EMISSIONS-TCO2E": ["GRI 305-1", "IFRS S2-1", "TCFD-Metrics-1", "CDP-C6.1", "NESREA-AIR-01", "SASB-EM-EP-110a.1", "CBN-ENV-01"],
    "ENV-S2-EMISSIONS-TCO2E": ["GRI 305-2", "IFRS S2-2", "TCFD-Metrics-1", "CDP-C6.3", "NSE-E-01"],
    "ENV-S3-EMISSIONS-TCO2E": ["GRI 305-3", "IFRS S2-3", "TCFD-Metrics-1", "FMENV-EM-01", "SDG-13.2", "SASB-EM-EP-130a.1"],
}


OPTIONAL_DERIVED_INDICATOR_MAPPING = {
    "ENV-TOTAL-EMISSIONS-TCO2E": ["TCFD-Metrics-1", "SDG-13.2", "CBN-ENV-01", "NSE-E-01", "FMENV-EM-01"],
}


def _build_input_indicator_mapping():
    """Build secondary mappings so each input maps to all relevant framework requirements.

    The source of truth is traceability (input -> derived) and primary derived mappings
    (derived -> framework requirements).
    """
    result = {}
    for input_indicator_code, derived_indicator_code in INPUT_TO_DERIVED_INDICATOR.items():
        requirement_codes = PRIMARY_DERIVED_INDICATOR_MAPPING.get(derived_indicator_code, [])
        if requirement_codes:
            result[input_indicator_code] = list(requirement_codes)
    return result


INPUT_INDICATOR_MAPPING = _build_input_indicator_mapping()


ACTIVITY_TYPES = [
    {
        "name": "Diesel Generator Usage",
        "description": "Capture diesel used by stationary generators.",
        "indicator_code": "S1-DIESEL-L",
        "data_type": ActivityType.DataType.NUMBER,
        "display_order": 10,
        "collection_frequency": ActivityType.CollectionFrequency.MONTHLY,
    },
    {
        "name": "Fleet Vehicle Usage",
        "description": "Capture diesel used by fleet vehicles.",
        "indicator_code": "S1-DIESEL-L",
        "data_type": ActivityType.DataType.NUMBER,
        "display_order": 20,
        "collection_frequency": ActivityType.CollectionFrequency.MONTHLY,
    },
    {
        "name": "LPG Usage",
        "description": "Capture LPG consumed in operations.",
        "indicator_code": "S1-LPG-KG",
        "data_type": ActivityType.DataType.NUMBER,
        "display_order": 30,
        "collection_frequency": ActivityType.CollectionFrequency.MONTHLY,
    },
    {
        "name": "Grid Electricity Consumption",
        "description": "Capture purchased grid electricity usage.",
        "indicator_code": "S2-ELEC-KWH",
        "data_type": ActivityType.DataType.NUMBER,
        "display_order": 40,
        "collection_frequency": ActivityType.CollectionFrequency.MONTHLY,
    },
    {
        "name": "Fertilizer Application",
        "description": "Capture fertilizer used in agricultural processes.",
        "indicator_code": "S3-FERT-KG",
        "data_type": ActivityType.DataType.NUMBER,
        "display_order": 50,
        "collection_frequency": ActivityType.CollectionFrequency.QUARTERLY,
    },
    {
        "name": "Livestock Feeding",
        "indicator_code": "S3-FEED-KG",
        "description": "Capture feed consumed in livestock operations.",
        "data_type": ActivityType.DataType.NUMBER,
        "display_order": 60,
        "collection_frequency": ActivityType.CollectionFrequency.MONTHLY,
    },
    {
        "name": "Waste Disposal",
        "description": "Capture waste volume disposed through approved channels.",
        "indicator_code": "S3-WASTE-M3",
        "data_type": ActivityType.DataType.NUMBER,
        "display_order": 70,
        "collection_frequency": ActivityType.CollectionFrequency.MONTHLY,
    },
    {
        "name": "Transport Logistics",
        "description": "Capture logistics transport distance across operations.",
        "indicator_code": "S3-TRANSPORT-KM",
        "data_type": ActivityType.DataType.NUMBER,
        "display_order": 80,
        "collection_frequency": ActivityType.CollectionFrequency.MONTHLY,
    },
]


LEGACY_GENERIC_ACTIVITY_NAMES = [
    "Fuel Consumption",
    "Electricity Usage",
    "Transport Activity",
    "Waste Management",
    "Agricultural Activity",
    "Livestock Activity",
]


class Command(BaseCommand):
    help = (
        "Seed global ESG master data: frameworks, framework requirements, "
        "indicators, indicator-framework mappings, and activity types."
    )

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write("Seeding global ESG master data...")

        scope, _ = Scope.objects.get_or_create(
            code="emissions",
            defaults={
                "name": "Emissions",
                "description": "Activities related to GHG and climate-related operations.",
            },
        )

        frameworks_by_code = {}
        for data in FRAMEWORKS:
            framework, created = RegulatoryFramework.objects.get_or_create(
                code=data["code"],
                defaults={
                    "name": data["name"],
                    "jurisdiction": data["jurisdiction"],
                    "description": data["description"],
                    "priority": data["priority"],
                    "is_active": True,
                    "is_system": True,
                },
            )
            if not created:
                framework.name = data["name"]
                framework.jurisdiction = data["jurisdiction"]
                framework.description = data["description"]
                framework.priority = data["priority"]
                framework.is_active = True
                framework.is_system = True
                framework.save(
                    update_fields=[
                        "name",
                        "jurisdiction",
                        "description",
                        "priority",
                        "is_active",
                        "is_system",
                        "updated_at",
                    ]
                )
            frameworks_by_code[data["code"]] = framework

        requirements_by_code = {}
        for fw_code, reqs in REQUIREMENTS.items():
            framework = frameworks_by_code[fw_code]
            for req in reqs:
                requirement, created = FrameworkRequirement.objects.get_or_create(
                    framework=framework,
                    code=req["code"],
                    defaults={
                        "title": req["title"],
                        "pillar": req["pillar"],
                        "is_mandatory": req["is_mandatory"],
                        "status": FrameworkRequirement.Status.ACTIVE,
                        "priority": 100 if req["is_mandatory"] else 50,
                    },
                )
                if not created:
                    requirement.title = req["title"]
                    requirement.pillar = req["pillar"]
                    requirement.is_mandatory = req["is_mandatory"]
                    requirement.status = FrameworkRequirement.Status.ACTIVE
                    requirement.priority = 100 if req["is_mandatory"] else 50
                    requirement.save(
                        update_fields=[
                            "title",
                            "pillar",
                            "is_mandatory",
                            "status",
                            "priority",
                            "updated_at",
                        ]
                    )
                requirements_by_code[req["code"]] = requirement

        indicators_by_code = {}

        for data in INPUT_INDICATORS:
            indicator, created = Indicator.objects.get_or_create(
                code=data["code"],
                defaults={
                    "name": data["name"],
                    "description": data["description"],
                    "pillar": data["pillar"],
                    "data_type": data["data_type"],
                    "unit": data["unit"],
                    "collection_method": Indicator.CollectionMethod.ACTIVITY,
                    "indicator_type": Indicator.IndicatorType.INPUT,
                    "emission_factor": None,
                    "calculation_method": None,
                    "is_active": True,
                },
            )
            if not created:
                indicator.name = data["name"]
                indicator.description = data["description"]
                indicator.pillar = data["pillar"]
                indicator.data_type = data["data_type"]
                indicator.unit = data["unit"]
                indicator.collection_method = Indicator.CollectionMethod.ACTIVITY
                indicator.indicator_type = Indicator.IndicatorType.INPUT
                indicator.emission_factor = None
                indicator.calculation_method = None
                indicator.is_active = True
                indicator.save(
                    update_fields=[
                        "name",
                        "description",
                        "pillar",
                        "data_type",
                        "unit",
                        "collection_method",
                        "indicator_type",
                        "emission_factor",
                        "calculation_method",
                        "is_active",
                        "updated_at",
                    ]
                )
            indicators_by_code[data["code"]] = indicator

        for data in DERIVED_INDICATORS:
            indicator, created = Indicator.objects.get_or_create(
                code=data["code"],
                defaults={
                    "name": data["name"],
                    "description": data["description"],
                    "pillar": data["pillar"],
                    "data_type": data["data_type"],
                    "unit": data["unit"],
                    "collection_method": Indicator.CollectionMethod.DIRECT,
                    "indicator_type": Indicator.IndicatorType.DERIVED,
                    "emission_factor": None,
                    "calculation_method": data["calculation_method"],
                    "is_active": True,
                },
            )
            if not created:
                indicator.name = data["name"]
                indicator.description = data["description"]
                indicator.pillar = data["pillar"]
                indicator.data_type = data["data_type"]
                indicator.unit = data["unit"]
                indicator.collection_method = Indicator.CollectionMethod.DIRECT
                indicator.indicator_type = Indicator.IndicatorType.DERIVED
                indicator.emission_factor = None
                indicator.calculation_method = data["calculation_method"]
                indicator.is_active = True
                indicator.save(
                    update_fields=[
                        "name",
                        "description",
                        "pillar",
                        "data_type",
                        "unit",
                        "collection_method",
                        "indicator_type",
                        "emission_factor",
                        "calculation_method",
                        "is_active",
                        "updated_at",
                    ]
                )
            indicators_by_code[data["code"]] = indicator

        mapping_created = 0
        primary_by_requirement = {}

        for indicator_code, requirement_codes in PRIMARY_DERIVED_INDICATOR_MAPPING.items():
            indicator = indicators_by_code[indicator_code]
            for requirement_code in requirement_codes:
                requirement = requirements_by_code[requirement_code]
                mapping, created = IndicatorFrameworkMapping.objects.get_or_create(
                    indicator=indicator,
                    framework=requirement.framework,
                    requirement=requirement,
                    defaults={
                        "mapping_type": IndicatorFrameworkMapping.MappingType.PRIMARY,
                        "is_primary": True,
                        "coverage_percent": 0,
                        "is_active": True,
                        "rationale": "Primary derived emissions indicator for requirement compliance.",
                    },
                )
                if not created:
                    mapping.mapping_type = IndicatorFrameworkMapping.MappingType.PRIMARY
                    mapping.coverage_percent = 0
                    mapping.is_active = True
                    mapping.is_primary = True
                    mapping.rationale = "Primary derived emissions indicator for requirement compliance."
                    mapping.save(
                        update_fields=[
                            "mapping_type",
                            "coverage_percent",
                            "is_active",
                            "is_primary",
                            "rationale",
                            "updated_at",
                        ]
                    )

                primary_by_requirement.setdefault(requirement_code, set()).add(indicator_code)

                if created:
                    mapping_created += 1

        for indicator_code, requirement_codes in OPTIONAL_DERIVED_INDICATOR_MAPPING.items():
            indicator = indicators_by_code[indicator_code]
            for requirement_code in requirement_codes:
                requirement = requirements_by_code[requirement_code]
                mapping, created = IndicatorFrameworkMapping.objects.get_or_create(
                    indicator=indicator,
                    framework=requirement.framework,
                    requirement=requirement,
                    defaults={
                        "mapping_type": IndicatorFrameworkMapping.MappingType.DERIVED,
                        "is_primary": False,
                        "coverage_percent": 0,
                        "is_active": True,
                        "rationale": "Derived analytics indicator; optional for contextual reporting.",
                    },
                )
                if not created:
                    mapping.mapping_type = IndicatorFrameworkMapping.MappingType.DERIVED
                    mapping.coverage_percent = 0
                    mapping.is_active = True
                    mapping.is_primary = False
                    mapping.rationale = "Derived analytics indicator; optional for contextual reporting."
                    mapping.save(
                        update_fields=[
                            "mapping_type",
                            "coverage_percent",
                            "is_active",
                            "is_primary",
                            "rationale",
                            "updated_at",
                        ]
                    )

                if created:
                    mapping_created += 1

        for indicator_code, requirement_codes in INPUT_INDICATOR_MAPPING.items():
            indicator = indicators_by_code[indicator_code]
            supporting_derived_code = INPUT_TO_DERIVED_INDICATOR.get(indicator_code)
            if not supporting_derived_code:
                raise CommandError(
                    f"Input indicator {indicator_code} has no derived traceability mapping"
                )

            for requirement_code in requirement_codes:
                requirement = requirements_by_code[requirement_code]
                requirement_primary_codes = primary_by_requirement.get(requirement_code, set())
                if supporting_derived_code not in requirement_primary_codes:
                    raise CommandError(
                        f"Secondary mapping {indicator_code}->{requirement_code} has no supporting primary derived mapping"
                    )

                mapping, created = IndicatorFrameworkMapping.objects.get_or_create(
                    indicator=indicator,
                    framework=requirement.framework,
                    requirement=requirement,
                    defaults={
                        "mapping_type": IndicatorFrameworkMapping.MappingType.SECONDARY,
                        "is_primary": False,
                        "coverage_percent": 0,
                        "is_active": True,
                        "rationale": f"Secondary input supporting derived indicator {supporting_derived_code}.",
                    },
                )
                if not created:
                    mapping.mapping_type = IndicatorFrameworkMapping.MappingType.SECONDARY
                    mapping.coverage_percent = 0
                    mapping.is_active = True
                    mapping.is_primary = False
                    mapping.rationale = f"Secondary input supporting derived indicator {supporting_derived_code}."
                    mapping.save(
                        update_fields=[
                            "mapping_type",
                            "coverage_percent",
                            "is_active",
                            "is_primary",
                            "rationale",
                            "updated_at",
                        ]
                    )

                if created:
                    mapping_created += 1

        invalid_primary_requirements = [
            requirement_code
            for requirement_code, requirement in requirements_by_code.items()
            if IndicatorFrameworkMapping.objects.filter(
                requirement=requirement,
                is_active=True,
                is_primary=True,
            ).exclude(
                indicator__indicator_type=Indicator.IndicatorType.DERIVED,
            ).exists()
        ]
        if invalid_primary_requirements:
            raise CommandError(
                "PRIMARY mappings must be DERIVED indicators only. "
                f"Invalid requirements: {', '.join(sorted(invalid_primary_requirements))}"
            )

        missing_primary_requirements = [
            requirement_code
            for requirement_code, requirement in requirements_by_code.items()
            if not IndicatorFrameworkMapping.objects.filter(
                requirement=requirement,
                is_active=True,
                is_primary=True,
                mapping_type=IndicatorFrameworkMapping.MappingType.PRIMARY,
                indicator__indicator_type=Indicator.IndicatorType.DERIVED,
            ).exists()
        ]
        if missing_primary_requirements:
            raise CommandError(
                "Each framework requirement must have at least one PRIMARY indicator. "
                f"Missing: {', '.join(sorted(missing_primary_requirements))}"
            )

        missing_secondary_requirements = [
            requirement_code
            for requirement_code, requirement in requirements_by_code.items()
            if not IndicatorFrameworkMapping.objects.filter(
                requirement=requirement,
                is_active=True,
                mapping_type=IndicatorFrameworkMapping.MappingType.SECONDARY,
            ).exists()
        ]
        if missing_secondary_requirements:
            self.stdout.write(
                self.style.WARNING(
                    "Recommended secondary input mappings are missing for requirements: "
                    f"{', '.join(sorted(missing_secondary_requirements))}"
                )
            )

        ActivityType.objects.filter(name__in=LEGACY_GENERIC_ACTIVITY_NAMES).delete()

        activity_created = 0
        for data in ACTIVITY_TYPES:
            indicator = indicators_by_code[data["indicator_code"]]
            activity, created = ActivityType.objects.get_or_create(
                name=data["name"],
                defaults={
                    "description": data["description"],
                    "unit": indicator.unit,
                    "scope": scope,
                    "display_order": data["display_order"],
                    "data_type": data["data_type"],
                    "collection_frequency": data["collection_frequency"],
                    "requires_evidence": False,
                    "is_required": False,
                    "is_active": True,
                    "indicator": indicator,
                },
            )
            if not created:
                activity.description = data["description"]
                activity.scope = scope
                activity.display_order = data["display_order"]
                activity.data_type = data["data_type"]
                activity.collection_frequency = data["collection_frequency"]
                activity.requires_evidence = False
                activity.is_required = False
                activity.is_active = True
                activity.indicator = indicator
                activity.save(
                    update_fields=[
                        "description",
                        "scope",
                        "display_order",
                        "data_type",
                        "collection_frequency",
                        "requires_evidence",
                        "is_required",
                        "is_active",
                        "indicator",
                        "updated_at",
                    ]
                )
            if created:
                activity_created += 1

        self.stdout.write(
            self.style.SUCCESS(
                "Seed complete: "
                f"frameworks={len(frameworks_by_code)}, "
                f"requirements={len(requirements_by_code)}, "
                f"indicators={len(INPUT_INDICATORS) + len(DERIVED_INDICATORS)}, "
                f"mappings={sum(len(v) for v in PRIMARY_DERIVED_INDICATOR_MAPPING.values()) + sum(len(v) for v in OPTIONAL_DERIVED_INDICATOR_MAPPING.values()) + sum(len(v) for v in INPUT_INDICATOR_MAPPING.values())}, "
                f"activity_types={len(ACTIVITY_TYPES)}"
            )
        )
        self.stdout.write(
            f"Created this run: mappings={mapping_created}, activity_types={activity_created}"
        )