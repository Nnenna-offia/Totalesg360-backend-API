"""Seed regulatory frameworks for Nigerian and international compliance."""
from django.core.management.base import BaseCommand
from django.db import transaction
from organizations.models import RegulatoryFramework


class Command(BaseCommand):
    help = "Seed regulatory frameworks for ESG compliance"

    def handle(self, *args, **options):
        self.stdout.write("Seeding regulatory frameworks...")
        self._seed_frameworks()
        self.stdout.write(self.style.SUCCESS("Successfully seeded regulatory frameworks"))

    @transaction.atomic
    def _seed_frameworks(self):
        """Create regulatory framework records."""
        frameworks_data = [
            # Nigerian Frameworks
            {
                "code": "NESREA",
                "name": "National Environmental Standards and Regulations Enforcement Agency",
                "jurisdiction": RegulatoryFramework.Jurisdiction.NIGERIA,
                "sector": "",  # Cross-sector
                "description": "Nigeria's primary environmental regulator enforcing environmental standards",
                "priority": 100,
            },
            {
                "code": "CBN_ESG",
                "name": "Central Bank of Nigeria ESG Guidelines",
                "jurisdiction": RegulatoryFramework.Jurisdiction.NIGERIA,
                "sector": "finance",
                "description": "CBN environmental and social risk management guidelines for financial institutions",
                "priority": 90,
            },
            {
                "code": "DPR",
                "name": "Department of Petroleum Resources",
                "jurisdiction": RegulatoryFramework.Jurisdiction.NIGERIA,
                "sector": "oil_gas",
                "description": "Regulates oil and gas environmental compliance in Nigeria",
                "priority": 90,
            },
            {
                "code": "NUPRC",
                "name": "Nigerian Upstream Petroleum Regulatory Commission",
                "jurisdiction": RegulatoryFramework.Jurisdiction.NIGERIA,
                "sector": "oil_gas",
                "description": "Regulates upstream petroleum operations including environmental standards",
                "priority": 85,
            },
            {
                "code": "FMEnv",
                "name": "Federal Ministry of Environment",
                "jurisdiction": RegulatoryFramework.Jurisdiction.NIGERIA,
                "sector": "",
                "description": "National environmental policy and EIA requirements",
                "priority": 80,
            },
            {
                "code": "NSE_ESG",
                "name": "Nigerian Exchange ESG Disclosure Guidelines",
                "jurisdiction": RegulatoryFramework.Jurisdiction.NIGERIA,
                "sector": "",
                "description": "ESG disclosure requirements for listed companies",
                "priority": 75,
            },
            
            # International Frameworks
            {
                "code": "GRI",
                "name": "Global Reporting Initiative (GRI Standards)",
                "jurisdiction": RegulatoryFramework.Jurisdiction.INTERNATIONAL,
                "sector": "",
                "description": "World's most widely used sustainability reporting standards",
                "priority": 100,
            },
            {
                "code": "ISSB",
                "name": "International Sustainability Standards Board (IFRS S1 & S2)",
                "jurisdiction": RegulatoryFramework.Jurisdiction.INTERNATIONAL,
                "sector": "",
                "description": "IFRS sustainability disclosure standards for capital markets",
                "priority": 95,
            },
            {
                "code": "TCFD",
                "name": "Task Force on Climate-related Financial Disclosures",
                "jurisdiction": RegulatoryFramework.Jurisdiction.INTERNATIONAL,
                "sector": "",
                "description": "Framework for climate-related financial risk disclosures",
                "priority": 90,
            },
            {
                "code": "SASB",
                "name": "Sustainability Accounting Standards Board",
                "jurisdiction": RegulatoryFramework.Jurisdiction.INTERNATIONAL,
                "sector": "",
                "description": "Industry-specific sustainability accounting standards",
                "priority": 85,
            },
            {
                "code": "CDP",
                "name": "Carbon Disclosure Project",
                "jurisdiction": RegulatoryFramework.Jurisdiction.INTERNATIONAL,
                "sector": "",
                "description": "Global disclosure system for environmental impact",
                "priority": 80,
            },
            {
                "code": "UN_SDG",
                "name": "UN Sustainable Development Goals",
                "jurisdiction": RegulatoryFramework.Jurisdiction.INTERNATIONAL,
                "sector": "",
                "description": "17 global goals for sustainable development",
                "priority": 75,
            },
            {
                "code": "ISO14001",
                "name": "ISO 14001 Environmental Management",
                "jurisdiction": RegulatoryFramework.Jurisdiction.INTERNATIONAL,
                "sector": "",
                "description": "International standard for environmental management systems",
                "priority": 70,
            },
            {
                "code": "IFC_PS",
                "name": "IFC Performance Standards",
                "jurisdiction": RegulatoryFramework.Jurisdiction.INTERNATIONAL,
                "sector": "",
                "description": "Environmental and social sustainability standards for private sector",
                "priority": 65,
            },
        ]

        for fw_data in frameworks_data:
            framework, created = RegulatoryFramework.objects.get_or_create(
                code=fw_data["code"],
                defaults={
                    "name": fw_data["name"],
                    "jurisdiction": fw_data["jurisdiction"],
                    "sector": fw_data["sector"],
                    "description": fw_data["description"],
                    "priority": fw_data["priority"],
                    "is_active": True,
                },
            )
            if created:
                self.stdout.write(f"  Created: {framework.code} - {framework.name}")
            else:
                self.stdout.write(f"  Already exists: {framework.code}")

        self.stdout.write(
            f"  Total frameworks: {RegulatoryFramework.objects.count()}"
        )
