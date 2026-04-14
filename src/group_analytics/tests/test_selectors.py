"""Test selectors for group analytics."""
from django.test import TestCase

from organizations.models import Organization, RegulatoryFramework, OrganizationFramework
from submissions.models import ReportingPeriod
from compliance.models import FrameworkReadiness, ComplianceGapPriority, ComplianceRecommendation, FrameworkRequirement
from esg_scoring.models import ESGScore
from group_analytics.selectors import (
    get_group_framework_readiness,
    get_group_top_gaps,
    get_group_recommendations,
    calculate_group_esg_score,
    get_subsidiary_ranking,
    get_group_dashboard,
)


class GroupReadinessTestCase(TestCase):
    """Test group framework readiness aggregation."""
    
    def setUp(self):
        """Set up test data."""
        # Create parent organization
        self.parent_org = Organization.objects.create(
            name='TGI Group',
            sector='oil_gas',
            country='NG',
            organization_type=Organization.OrganizationType.GROUP,
        )
        
        # Create subsidiaries
        self.subsidiary_1 = Organization.objects.create(
            name='Subsidiary 1',
            sector='oil_gas',
            country='NG',
            parent=self.parent_org,
            organization_type=Organization.OrganizationType.SUBSIDIARY,
        )
        
        self.subsidiary_2 = Organization.objects.create(
            name='Subsidiary 2',
            sector='oil_gas',
            country='NG',
            parent=self.parent_org,
            organization_type=Organization.OrganizationType.SUBSIDIARY,
        )
        
        # Create framework
        self.framework = RegulatoryFramework.objects.create(
            code='GRI',
            name='Global Reporting Initiative',
            jurisdiction='INTERNATIONAL',
        )
        
        # Create reporting period
        from datetime import date, timedelta
        today = date.today()
        self.reporting_period = ReportingPeriod.objects.create(
            organization=self.parent_org,
            name='Annual 2025',
            period_type='ANNUAL',
            start_date=today - timedelta(days=365),
            end_date=today,
        )
    
    def test_get_group_framework_readiness(self):
        """Test group readiness aggregation."""
        # Create readiness scores for subsidiaries
        FrameworkReadiness.objects.create(
            organization=self.subsidiary_1,
            framework=self.framework,
            reporting_period=self.reporting_period,
            total_requirements=10,
            covered_requirements=7,
            coverage_percent=70.0,
            mandatory_requirements=5,
            mandatory_covered=4,
            mandatory_coverage_percent=80.0,
            readiness_score=74.0,
            risk_level='medium',
        )
        
        FrameworkReadiness.objects.create(
            organization=self.subsidiary_2,
            framework=self.framework,
            reporting_period=self.reporting_period,
            total_requirements=10,
            covered_requirements=8,
            coverage_percent=80.0,
            mandatory_requirements=5,
            mandatory_covered=5,
            mandatory_coverage_percent=100.0,
            readiness_score=85.0,
            risk_level='low',
        )
        
        # Get group readiness
        readiness = get_group_framework_readiness(self.parent_org, self.reporting_period)
        
        self.assertIsNotNone(readiness)
        self.assertEqual(len(readiness['frameworks']), 1)
        
        framework_data = readiness['frameworks'][0]
        self.assertEqual(framework_data['code'], 'GRI')
        self.assertEqual(framework_data['subsidiary_count'], 2)
        # Average: (70 + 80) / 2 = 75
        self.assertAlmostEqual(framework_data['avg_readiness'], 75.0, places=1)


class GroupESGScoreTestCase(TestCase):
    """Test group ESG score aggregation."""
    
    def setUp(self):
        """Set up test data."""
        self.parent_org = Organization.objects.create(
            name='TGI Group',
            sector='manufacturing',
            country='NG',
            organization_type=Organization.OrganizationType.GROUP,
        )
        
        self.subsidiary_1 = Organization.objects.create(
            name='Subsidiary 1',
            sector='manufacturing',
            country='NG',
            parent=self.parent_org,
            organization_type=Organization.OrganizationType.SUBSIDIARY,
        )
        
        self.subsidiary_2 = Organization.objects.create(
            name='Subsidiary 2',
            sector='manufacturing',
            country='NG',
            parent=self.parent_org,
            organization_type=Organization.OrganizationType.SUBSIDIARY,
        )
        
        from datetime import date, timedelta
        today = date.today()
        self.reporting_period = ReportingPeriod.objects.create(
            organization=self.parent_org,
            name='Annual 2025',
            period_type='ANNUAL',
            start_date=today - timedelta(days=365),
            end_date=today,
        )
    
    def test_calculate_group_esg_score(self):
        """Test group ESG score calculation."""
        # Create ESG scores for subsidiaries
        ESGScore.objects.create(
            organization=self.subsidiary_1,
            reporting_period=self.reporting_period,
            environmental_score=40.0,
            social_score=45.0,
            governance_score=38.0,
            overall_score=41.0,
            is_consolidated=False,
        )
        
        ESGScore.objects.create(
            organization=self.subsidiary_2,
            reporting_period=self.reporting_period,
            environmental_score=50.0,
            social_score=55.0,
            governance_score=52.0,
            overall_score=52.0,
            is_consolidated=False,
        )
        
        # Calculate group score
        group_score = calculate_group_esg_score(self.parent_org, self.reporting_period)
        
        self.assertIsNotNone(group_score)
        self.assertEqual(group_score['subsidiary_count'], 2)
        # Average: (40 + 50) / 2 = 45
        self.assertAlmostEqual(group_score['environmental'], 45.0, places=1)
        # Average: (45 + 55) / 2 = 50
        self.assertAlmostEqual(group_score['social'], 50.0, places=1)
        # Average: (38 + 52) / 2 = 45
        self.assertAlmostEqual(group_score['governance'], 45.0, places=1)
        # Average: (41 + 52) / 2 = 46.5
        self.assertAlmostEqual(group_score['overall'], 46.5, places=1)


class GroupDashboardTestCase(TestCase):
    """Test group dashboard."""
    
    def setUp(self):
        """Set up test data."""
        self.parent_org = Organization.objects.create(
            name='TGI Group',
            sector='manufacturing',
            country='NG',
            organization_type=Organization.OrganizationType.GROUP,
        )
    
    def test_get_group_dashboard_empty(self):
        """Test getting dashboard with no data."""
        dashboard = get_group_dashboard(self.parent_org)
        
        self.assertIsNotNone(dashboard)
        self.assertEqual(dashboard['total_subsidiaries'], 0)
        self.assertIsNone(dashboard['esg_score'])
