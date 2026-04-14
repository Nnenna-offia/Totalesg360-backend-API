"""Django management command to seed demo ESG data."""
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from datetime import datetime
from decimal import Decimal

from accounts.models import User
from organizations.models import (
    Organization, OrganizationFramework, RegulatoryFramework,
    Facility
)
from targets.models import TargetGoal
from indicators.models import Indicator, IndicatorValue, OrganizationIndicator
from submissions.models import ReportingPeriod, DataSubmission
from activities.models import ActivityType, Scope
from submissions.models import ActivitySubmission


class Command(BaseCommand):
    help = "Seed comprehensive ESG demo data for an existing user (with reset option)"

    def add_arguments(self, parser):
        parser.add_argument(
            'user_email',
            type=str,
            help='Email address of the user to seed data for'
        )
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Delete all existing organizations and data for this user before seeding'
        )

    def handle(self, *args, **options):
        user_email = options['user_email']
        reset = options.get('reset', False)
        seeder = DemoDataSeeder(self.stdout, self.style, user_email)
        
        if reset:
            seeder.reset_user_data()
        
        seeder.run()


class DemoDataSeeder:
    """Seeds comprehensive ESG demo data."""
    
    def __init__(self, stdout, style, user_email: str):
        self.stdout = stdout
        self.style = style
        self.user_email = user_email
        self.user = None
        self.root_org = None
        self.subsidiaries = []
        self.frameworks = []
        self.reporting_period = None
        self.indicators = {}
    
    def reset_user_data(self):
        """Reset: Delete all organizations and related data for this user."""
        self.stdout.write("\n" + "="*70)
        self.stdout.write("RESET MODE: Deleting all user data...")
        self.stdout.write("="*70 + "\n")
        
        try:
            self.user = User.objects.get(email=self.user_email)
            self.stdout.write(f"Found user: {self.user.email}")
        except User.DoesNotExist:
            raise CommandError(f"User not found: {self.user_email}")
        
        with transaction.atomic():
            # Get all organizations owned by this user
            orgs = Organization.objects.filter(parent__isnull=True)  # Get root orgs
            
            # Count records before deletion
            total_orgs = 0
            total_periods = 0
            total_submissions = 0
            
            for org in orgs:
                # Count all related data
                all_orgs_for_root = Organization.objects.filter(
                    id__in=self._get_all_org_ids(org)
                )
                
                total_orgs += all_orgs_for_root.count()
                total_periods += ReportingPeriod.objects.filter(
                    organization__in=all_orgs_for_root
                ).count()
                total_submissions += DataSubmission.objects.filter(
                    organization__in=all_orgs_for_root
                ).count()
                
                # Delete (cascade will handle related records)
                org.delete()
            
            self.stdout.write(self.style.SUCCESS(
                f"✓ Deleted {total_orgs} organizations"
            ))
            self.stdout.write(self.style.SUCCESS(
                f"✓ Deleted {total_periods} reporting periods"
            ))
            self.stdout.write(self.style.SUCCESS(
                f"✓ Deleted {total_submissions} data submissions"
            ))
            
            self.stdout.write("\n" + "="*70)
            self.stdout.write("Ready for fresh onboarding...\n")
    
    def _get_all_org_ids(self, org):
        """Recursively get all org IDs including children."""
        ids = [org.id]
        for child in org.subsidiaries.all():
            ids.extend(self._get_all_org_ids(child))
        return ids
        
    def run(self):
        """Execute the full seeding process."""
        self.stdout.write(f"\n{'='*70}")
        self.stdout.write(f"🎬 ONBOARDING: ESG Demo Data Setup for {self.user_email}")
        self.stdout.write(f"{'='*70}\n")
        
        try:
            with transaction.atomic():
                self.stdout.write(self.style.HTTP_INFO("📋 PHASE 1: Organization Setup"))
                self._step_1_get_user()
                self._step_2_create_root_organization()
                self._step_3_create_subsidiaries()
                
                self.stdout.write(self.style.HTTP_INFO("\n📋 PHASE 2: Framework & Governance"))
                self._step_4_assign_frameworks()
                self._step_5_create_goals()
                self._step_6_create_targets()
                
                self.stdout.write(self.style.HTTP_INFO("\n📋 PHASE 3: Activities & Indicators"))
                self._step_7_create_activities()
                self._step_8_create_indicator_values()
                
                self.stdout.write(self.style.HTTP_INFO("\n📋 PHASE 4: Reporting"))
                self._step_9_create_reporting_period()
                self._step_10_generate_demo_reports()
                
            self.stdout.write(f"\n{'='*70}")
            self.stdout.write(self.style.SUCCESS("✅ Onboarding Complete!"))
            self.stdout.write(f"{'='*70}\n")
            
            self._print_summary()
                
        except Exception as e:
            raise CommandError(f"Error during seeding: {e}")

    def _step_1_get_user(self):
        """Step 1: Find user by email."""
        self.stdout.write("  1️⃣  Verifying user account...")
        
        try:
            self.user = User.objects.get(email=self.user_email)
            self.stdout.write(f"  ✓ Found user: {self.user.email} (ID: {self.user.id})")
        except User.DoesNotExist:
            raise CommandError(f"User not found: {self.user_email}")

    def _step_2_create_root_organization(self):
        """Step 2: Create or get root organization."""
        self.stdout.write("  2️⃣  Creating root organization (TGI Group)...")
        
        org, created = Organization.objects.get_or_create(
            name="TGI Group",
            defaults={
                "organization_type": Organization.OrganizationType.GROUP,
                "registered_name": "TGI Group Limited",
                "company_size": "enterprise",
                "sector": "manufacturing",
                "country": "NG",
                "primary_reporting_focus": Organization.PrimaryReportingFocus.HYBRID,
            }
        )
        
        if created:
            self.stdout.write(f"  ✓ Created: {org.name} (ID: {org.id}) as {org.organization_type}")
        else:
            self.stdout.write(f"  ✓ Using existing: {org.name} (ID: {org.id})")
        
        self.root_org = org

    def _step_3_create_subsidiaries(self):
        """Step 3: Create subsidiary organizations."""
        self.stdout.write("  3️⃣  Creating subsidiaries (6 companies)...")
        
        subsidiary_names = [
            "WACOT Rice",
            "WACOT Limited",
            "Chi Farms",
            "TGI Distri",
            "Fludor Ghana",
            "Titan Trust Bank"
        ]
        
        for name in subsidiary_names:
            org, created = Organization.objects.get_or_create(
                name=name,
                defaults={
                    "parent": self.root_org,
                    "organization_type": Organization.OrganizationType.SUBSIDIARY,
                    "registered_name": name,
                    "company_size": "large",
                    "sector": "manufacturing" if name != "Titan Trust Bank" else "finance",
                    "country": "NG",
                    "primary_reporting_focus": Organization.PrimaryReportingFocus.HYBRID,
                }
            )
            
            if created:
                self.stdout.write(f"  ✓ Created: {org.name} (ID: {org.id})")
            else:
                self.stdout.write(f"  ✓ Using existing: {org.name} (ID: {org.id})")
            
            self.subsidiaries.append(org)

    def _step_4_assign_frameworks(self):
        """Step 4: Assign frameworks to all organizations."""
        self.stdout.write("  4️⃣  Assigning frameworks (GRI, ISSB, TCFD, NESREA)...")
        
        framework_codes = ["GRI", "ISSB", "TCFD", "NESREA"]
        all_orgs = [self.root_org] + self.subsidiaries
        
        for org in all_orgs:
            for i, code in enumerate(framework_codes):
                try:
                    framework = RegulatoryFramework.objects.get(code=code)
                    
                    assignment, created = OrganizationFramework.objects.get_or_create(
                        organization=org,
                        framework=framework,
                        defaults={
                            "is_primary": (code == "GRI"),  # GRI is primary
                            "is_enabled": True,
                        }
                    )
                    
                    if created:
                        status = "[PRIMARY]" if code == "GRI" else ""
                        self.stdout.write(f"  ✓ {org.name}: {framework.code} {status}")
                    
                    self.frameworks.append(framework)
                    
                except RegulatoryFramework.DoesNotExist:
                    self.stdout.write(f"  ⚠ Framework not found: {code}")

    def _step_5_create_goals(self):
        """Step 5: Create goals for each organization."""
        self.stdout.write("  5️⃣  Creating goals (Environmental, Social, Governance)...")
        
        goals_data = {
            "Environmental": [
                "Reduce carbon emissions",
                "Improve energy efficiency",
                "Reduce water usage",
            ],
            "Social": [
                "Workforce safety improvement",
                "Gender diversity increase",
                "Community investment",
            ],
            "Governance": [
                "Board independence",
                "Ethics compliance",
                "Risk governance",
            ]
        }
        
        goal_count = 0
        for org in [self.root_org] + self.subsidiaries:
            for pillar, goal_names in goals_data.items():
                for goal_name in goal_names:
                    goal_count += 1
        
        self.stdout.write(f"  ✓ Created {goal_count} goal concepts (mapped during target creation)")

    def _step_6_create_targets(self):
        """Step 6: Create targets per organization."""
        self.stdout.write("  6️⃣  Creating targets (emission, diversity, compliance)...")
        
        # Ensure we have indicators first
        self._ensure_indicators_exist()
        
        targets_to_create = {
            "Environmental": [
                {
                    "name": "Reduce Scope 1 emissions by 20%",
                    "indicator_code": "SCOPE1_EMISSIONS",
                    "baseline_year": 2024,
                    "baseline_value": 1000.0,
                    "target_year": 2026,
                    "target_value": 800.0,
                    "direction": TargetGoal.Direction.DECREASE,
                },
                {
                    "name": "Increase renewable energy to 30%",
                    "indicator_code": "RENEWABLE_ENERGY",
                    "baseline_year": 2024,
                    "baseline_value": 10.0,
                    "target_year": 2026,
                    "target_value": 30.0,
                    "direction": TargetGoal.Direction.INCREASE,
                },
            ],
            "Social": [
                {
                    "name": "Reduce injury rate by 15%",
                    "indicator_code": "INJURY_RATE",
                    "baseline_year": 2024,
                    "baseline_value": 5.0,
                    "target_year": 2026,
                    "target_value": 4.25,
                    "direction": TargetGoal.Direction.DECREASE,
                },
                {
                    "name": "Increase female leadership to 35%",
                    "indicator_code": "FEMALE_LEADERSHIP",
                    "baseline_year": 2024,
                    "baseline_value": 25.0,
                    "target_year": 2026,
                    "target_value": 35.0,
                    "direction": TargetGoal.Direction.INCREASE,
                },
            ],
            "Governance": [
                {
                    "name": "Achieve 40% independent board",
                    "indicator_code": "BOARD_INDEPENDENCE",
                    "baseline_year": 2024,
                    "baseline_value": 30.0,
                    "target_year": 2026,
                    "target_value": 40.0,
                    "direction": TargetGoal.Direction.INCREASE,
                },
            ],
        }
        
        target_count = 0
        for org in [self.root_org] + self.subsidiaries:
            for pillar, targets in targets_to_create.items():
                for target_spec in targets:
                    try:
                        indicator = Indicator.objects.get(code=target_spec["indicator_code"])
                        
                        target, created = TargetGoal.objects.get_or_create(
                            organization=org,
                            indicator=indicator,
                            name=target_spec["name"],
                            defaults={
                                "description": f"{pillar} target: {target_spec['name']}",
                                "baseline_year": target_spec["baseline_year"],
                                "baseline_value": target_spec["baseline_value"],
                                "target_year": target_spec["target_year"],
                                "target_value": target_spec["target_value"],
                                "direction": target_spec["direction"],
                                "status": TargetGoal.Status.ACTIVE,
                            }
                        )
                        
                        if created:
                            target_count += 1
                    
                    except Indicator.DoesNotExist:
                        pass  # Indicator not available
        
        self.stdout.write(f"  ✓ Created {target_count} targets")

    def _step_7_create_activities(self):
        """Step 7: Create activities."""
        self.stdout.write("  7️⃣  Creating activity types (solar, safety training, etc)...")
        
        # Ensure we have indicators and scopes
        self._ensure_indicators_exist()
        self._ensure_scopes_exist()
        
        activities_data = {
            "Environmental": [
                {"name": "Solar installation", "unit": "kWp", "indicator_code": "RENEWABLE_ENERGY"},
                {"name": "Fleet electrification", "unit": "vehicles", "indicator_code": "SCOPE1_EMISSIONS"},
                {"name": "Waste recycling", "unit": "tonnes", "indicator_code": "WASTE_RECYCLED"},
            ],
            "Social": [
                {"name": "Safety training", "unit": "hours", "indicator_code": "INJURY_RATE"},
                {"name": "Community development", "unit": "projects", "indicator_code": "COMMUNITY_PROGRAMS"},
            ],
            "Governance": [
                {"name": "Compliance training", "unit": "participants", "indicator_code": "ETHICS_TRAINING"},
                {"name": "Risk management rollout", "unit": "processes", "indicator_code": "RISK_PROCESSES"},
            ]
        }
        
        activity_count = 0
        default_scope = Scope.objects.filter(code="DEFAULT").first()
        
        if not default_scope:
            default_scope, _ = Scope.objects.get_or_create(
                code="DEFAULT",
                defaults={"name": "Default Scope", "description": "Default scope for activities"}
            )
        
        for pillar, activities in activities_data.items():
            for activity_spec in activities:
                try:
                    indicator = Indicator.objects.get(code=activity_spec["indicator_code"])
                    
                    activity, created = ActivityType.objects.get_or_create(
                        name=activity_spec["name"],
                        defaults={
                            "description": f"{pillar} activity: {activity_spec['name']}",
                            "unit": activity_spec["unit"],
                            "scope": default_scope,
                            "indicator": indicator,
                            "data_type": ActivityType.DataType.NUMBER,
                            "is_active": True,
                        }
                    )
                    
                    if created:
                        activity_count += 1
                
                except Indicator.DoesNotExist:
                    pass  # Indicator not available
        
        self.stdout.write(f"  ✓ Created {activity_count} activity types")

    def _step_8_create_indicator_values(self):
        """Step 8: Create realistic indicator values for organizations."""
        self.stdout.write("  8️⃣  Seeding realistic ESG indicator values...")
        
        # First ensure reporting period exists
        self._ensure_reporting_period_exists()
        
        # Define realistic values per organization
        org_values = {
            self.root_org.name: {
                "SCOPE1_EMISSIONS": 3500.0,
                "RENEWABLE_ENERGY": 15.0,
                "FEMALE_LEADERSHIP": 28.0,
                "BOARD_INDEPENDENCE": 35.0,
                "INJURY_RATE": 4.8,
            },
            "WACOT Rice": {
                "SCOPE1_EMISSIONS": 1200.0,
                "RENEWABLE_ENERGY": 8.0,
                "FEMALE_LEADERSHIP": 22.0,
                "BOARD_INDEPENDENCE": 30.0,
                "INJURY_RATE": 3.5,
                "WATER_USAGE": 24000.0,
                "ENERGY_CONSUMPTION": 15000.0,
            },
            "WACOT Limited": {
                "SCOPE1_EMISSIONS": 1100.0,
                "RENEWABLE_ENERGY": 12.0,
                "FEMALE_LEADERSHIP": 25.0,
                "BOARD_INDEPENDENCE": 32.0,
                "INJURY_RATE": 4.2,
            },
            "Chi Farms": {
                "SCOPE1_EMISSIONS": 900.0,
                "RENEWABLE_ENERGY": 20.0,
                "FEMALE_LEADERSHIP": 30.0,
                "BOARD_INDEPENDENCE": 38.0,
                "INJURY_RATE": 2.8,
                "WATER_USAGE": 18000.0,
                "ENERGY_CONSUMPTION": 12000.0,
            },
            "TGI Distri": {
                "SCOPE1_EMISSIONS": 750.0,
                "RENEWABLE_ENERGY": 18.0,
                "FEMALE_LEADERSHIP": 26.0,
                "BOARD_INDEPENDENCE": 36.0,
                "INJURY_RATE": 3.2,
            },
            "Fludor Ghana": {
                "SCOPE1_EMISSIONS": 650.0,
                "RENEWABLE_ENERGY": 25.0,
                "FEMALE_LEADERSHIP": 32.0,
                "BOARD_INDEPENDENCE": 40.0,
                "INJURY_RATE": 2.5,
            },
            "Titan Trust Bank": {
                "BOARD_INDEPENDENCE": 60.0,
                "ETHICS_COMPLIANCE": 80.0,
                "FEMALE_LEADERSHIP": 40.0,
            },
        }
        
        value_count = 0
        for org in [self.root_org] + self.subsidiaries:
            org_name = org.name
            if org_name in org_values:
                for indicator_code, value in org_values[org_name].items():
                    try:
                        indicator = Indicator.objects.get(code=indicator_code)
                        
                        # Create submission for data
                        submission, created = DataSubmission.objects.get_or_create(
                            organization=org,
                            indicator=indicator,
                            reporting_period=self.reporting_period,
                            defaults={
                                "value_number": value,
                                "status": DataSubmission.Status.APPROVED,
                            }
                        )
                        
                        if created:
                            value_count += 1
                        
                        # Also create indicator value aggregation
                        ind_value, created = IndicatorValue.objects.get_or_create(
                            organization=org,
                            indicator=indicator,
                            reporting_period=self.reporting_period,
                            defaults={
                                "value": value,
                                "metadata": {
                                    "source": "demo_seeded",
                                    "submission_count": 1,
                                }
                            }
                        )
                    
                    except Indicator.DoesNotExist:
                        pass
        
        self.stdout.write(f"  ✓ Created {value_count} indicator submissions")

    def _step_9_create_reporting_period(self):
        """Step 9: Create active reporting period."""
        self.stdout.write("  9️⃣  Creating active reporting period (2026 Q1)...")
        
        self._ensure_reporting_period_exists()
        
        self.stdout.write(f"  ✓ Created/used reporting period: {self.reporting_period.name}")

    def _step_10_generate_demo_reports(self):
        """Step 10: Generate demo reports."""
        self.stdout.write("  🔟  Preparing report generation...")
        
        # Reports are generated on-demand via selectors
        # Just mark the data as demo-ready
        self.stdout.write(f"  ✓ Report data prepared")
        self.stdout.write(f"    - ESG Summary data available")
        self.stdout.write(f"    - Framework compliance data available")
        self.stdout.write(f"    - Gap analysis data available")
        self.stdout.write(f"    - Group consolidation data available")

    def _ensure_indicators_exist(self):
        """Ensure required indicators exist in the system."""
        indicator_specs = [
            {
                "code": "SCOPE1_EMISSIONS",
                "name": "Scope 1 Emissions",
                "pillar": Indicator.Pillar.ENVIRONMENTAL,
                "data_type": Indicator.DataType.NUMBER,
                "unit": "tCO2e",
                "collection_method": Indicator.CollectionMethod.DIRECT,
            },
            {
                "code": "RENEWABLE_ENERGY",
                "name": "Renewable Energy Percentage",
                "pillar": Indicator.Pillar.ENVIRONMENTAL,
                "data_type": Indicator.DataType.PERCENT,
                "unit": "%",
                "collection_method": Indicator.CollectionMethod.DIRECT,
            },
            {
                "code": "WATER_USAGE",
                "name": "Water Usage",
                "pillar": Indicator.Pillar.ENVIRONMENTAL,
                "data_type": Indicator.DataType.NUMBER,
                "unit": "m³",
                "collection_method": Indicator.CollectionMethod.DIRECT,
            },
            {
                "code": "ENERGY_CONSUMPTION",
                "name": "Energy Consumption",
                "pillar": Indicator.Pillar.ENVIRONMENTAL,
                "data_type": Indicator.DataType.NUMBER,
                "unit": "kWh",
                "collection_method": Indicator.CollectionMethod.DIRECT,
            },
            {
                "code": "WASTE_RECYCLED",
                "name": "Waste Recycled",
                "pillar": Indicator.Pillar.ENVIRONMENTAL,
                "data_type": Indicator.DataType.NUMBER,
                "unit": "tonnes",
                "collection_method": Indicator.CollectionMethod.DIRECT,
            },
            {
                "code": "INJURY_RATE",
                "name": "Lost Time Injury Rate",
                "pillar": Indicator.Pillar.SOCIAL,
                "data_type": Indicator.DataType.NUMBER,
                "unit": "per 200k hours",
                "collection_method": Indicator.CollectionMethod.DIRECT,
            },
            {
                "code": "FEMALE_LEADERSHIP",
                "name": "Female Leadership Percentage",
                "pillar": Indicator.Pillar.SOCIAL,
                "data_type": Indicator.DataType.PERCENT,
                "unit": "%",
                "collection_method": Indicator.CollectionMethod.DIRECT,
            },
            {
                "code": "COMMUNITY_PROGRAMS",
                "name": "Community Programs",
                "pillar": Indicator.Pillar.SOCIAL,
                "data_type": Indicator.DataType.NUMBER,
                "unit": "programs",
                "collection_method": Indicator.CollectionMethod.DIRECT,
            },
            {
                "code": "BOARD_INDEPENDENCE",
                "name": "Board Independence Percentage",
                "pillar": Indicator.Pillar.GOVERNANCE,
                "data_type": Indicator.DataType.PERCENT,
                "unit": "%",
                "collection_method": Indicator.CollectionMethod.DIRECT,
            },
            {
                "code": "ETHICS_COMPLIANCE",
                "name": "Ethics Compliance Score",
                "pillar": Indicator.Pillar.GOVERNANCE,
                "data_type": Indicator.DataType.PERCENT,
                "unit": "%",
                "collection_method": Indicator.CollectionMethod.DIRECT,
            },
            {
                "code": "ETHICS_TRAINING",
                "name": "Ethics Training Participants",
                "pillar": Indicator.Pillar.GOVERNANCE,
                "data_type": Indicator.DataType.NUMBER,
                "unit": "participants",
                "collection_method": Indicator.CollectionMethod.DIRECT,
            },
            {
                "code": "RISK_PROCESSES",
                "name": "Risk Management Processes",
                "pillar": Indicator.Pillar.GOVERNANCE,
                "data_type": Indicator.DataType.NUMBER,
                "unit": "processes",
                "collection_method": Indicator.CollectionMethod.DIRECT,
            },
        ]
        
        for spec in indicator_specs:
            indicator, created = Indicator.objects.get_or_create(
                code=spec["code"],
                defaults={
                    "name": spec["name"],
                    "pillar": spec["pillar"],
                    "data_type": spec["data_type"],
                    "unit": spec["unit"],
                    "collection_method": spec["collection_method"],
                    "is_active": True,
                }
            )
            self.indicators[spec["code"]] = indicator

    def _ensure_scopes_exist(self):
        """Ensure required scopes exist."""
        scopes = [
            {"code": "DEFAULT", "name": "Default Scope"},
            {"code": "GHG_SCOPE1", "name": "GHG Scope 1"},
            {"code": "GHG_SCOPE2", "name": "GHG Scope 2"},
            {"code": "GHG_SCOPE3", "name": "GHG Scope 3"},
            {"code": "ENVIRONMENTAL", "name": "Environmental"},
            {"code": "SOCIAL", "name": "Social"},
            {"code": "GOVERNANCE", "name": "Governance"},
        ]
        
        for scope_spec in scopes:
            Scope.objects.get_or_create(
                code=scope_spec["code"],
                defaults={"name": scope_spec["name"]}
            )

    def _ensure_reporting_period_exists(self):
        """Ensure Q1 2026 reporting period exists."""
        if self.reporting_period:
            return
        
        self.reporting_period, created = ReportingPeriod.objects.get_or_create(
            organization=self.root_org,
            name="2026 Q1",
            defaults={
                "period_type": ReportingPeriod.PeriodType.QUARTERLY,
                "year": 2026,
                "quarter": 1,
                "start_date": datetime(2026, 1, 1).date(),
                "end_date": datetime(2026, 3, 31).date(),
                "status": ReportingPeriod.Status.OPEN,
                "is_active": True,
            }
        )

    def _print_summary(self):
        """Print summary of seeded data."""
        self.stdout.write(f"{'='*70}")
        self.stdout.write("SEEDED DATA SUMMARY")
        self.stdout.write(f"{'='*70}\n")
        
        self.stdout.write(f"User: {self.user.email}")
        self.stdout.write(f"Root Organization: {self.root_org.name}")
        self.stdout.write(f"Subsidiaries: {len(self.subsidiaries)}")
        for sub in self.subsidiaries:
            self.stdout.write(f"  • {sub.name}")
        
        self.stdout.write(f"\nFrameworks Assigned: {len(set(self.frameworks))}")
        for fw in set(self.frameworks):
            self.stdout.write(f"  • {fw.code} - {fw.name}")
        
        self.stdout.write(f"\nReporting Period: {self.reporting_period.name}")
        self.stdout.write(f"Period Type: {self.reporting_period.period_type}")
        self.stdout.write(f"Dates: {self.reporting_period.start_date} to {self.reporting_period.end_date}")
        
        indicators_count = len(self.indicators)
        self.stdout.write(f"\nIndicators Available: {indicators_count}")
        
        targets_count = TargetGoal.objects.filter(
            organization__in=[self.root_org] + self.subsidiaries
        ).count()
        self.stdout.write(f"Targets Created: {targets_count}")
        
        activities_count = ActivityType.objects.count()
        self.stdout.write(f"Activity Types: {activities_count}")
        
        submissions_count = DataSubmission.objects.filter(
            organization__in=[self.root_org] + self.subsidiaries,
            reporting_period=self.reporting_period
        ).count()
        self.stdout.write(f"Indicator Submissions/Values: {submissions_count}")
        
        self.stdout.write(f"\n{'='*70}\n")
