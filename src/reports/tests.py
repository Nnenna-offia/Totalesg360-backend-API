"""Tests for reports app."""
from django.test import TestCase
from datetime import date, timedelta
import uuid

from organizations.models import Organization, RegulatoryFramework
from submissions.models import ReportingPeriod
from esg_scoring.models import ESGScore
from compliance.models import FrameworkReadiness, ComplianceGapPriority, ComplianceRecommendation, FrameworkRequirement
from reports.models import Report
from reports.services import generate_report
from reports.selectors import (
    get_esg_summary_report,
    get_framework_report,
    get_group_esg_report,
    get_gap_report,
    get_partner_report,
)


class ESGSummaryReportTestCase(TestCase):
    """Test ESG summary report generation."""
    
    def setUp(self):
        """Set up test data."""
        self.org = Organization.objects.create(
            name='Test Org',
            sector='manufacturing',
            country='NG',
            organization_type=Organization.OrganizationType.SUBSIDIARY,
        )
        
        today = date.today()
        self.period = ReportingPeriod.objects.create(
            organization=self.org,
            name='2026 Annual',
            period_type='ANNUAL',
            start_date=today - timedelta(days=365),
            end_date=today,
        )
        
        # Create ESG score
        self.esg_score = ESGScore.objects.create(
            organization=self.org,
            reporting_period=self.period,
            environmental_score=40.0,
            social_score=45.0,
            governance_score=42.0,
            overall_score=42.3,
        )
        
        # Create framework
        self.framework = RegulatoryFramework.objects.create(
            code='GRI',
            name='Global Reporting Initiative',
            jurisdiction='INTERNATIONAL',
        )
        
        # Create framework readiness
        self.readiness = FrameworkReadiness.objects.create(
            organization=self.org,
            framework=self.framework,
            reporting_period=self.period,
            total_requirements=100,
            covered_requirements=62,
            coverage_percent=62.0,
            mandatory_requirements=50,
            mandatory_covered=40,
            mandatory_coverage_percent=80.0,
            readiness_score=74.0,
            risk_level='medium',
        )
    
    def test_get_esg_summary_report(self):
        """Test ESG summary report aggregation."""
        report = get_esg_summary_report(self.org, self.period)
        
        self.assertIsNotNone(report)
        self.assertEqual(report['organization'], 'Test Org')
        self.assertEqual(report['esg_score']['environmental'], 40.0)
        self.assertEqual(report['esg_score']['social'], 45.0)
        self.assertEqual(report['esg_score']['overall'], 42.3)
        self.assertEqual(len(report['framework_readiness']), 1)
        self.assertEqual(report['framework_readiness'][0]['framework'], 'GRI')
        self.assertEqual(report['summary']['overall_esg_rating'], 'MODERATE')


class FrameworkReportTestCase(TestCase):
    """Test framework report generation."""
    
    def    setUp(self):
        """Set up test data."""
        self.org = Organization.objects.create(
            name='Test Org',
            sector='oil_gas',
            country='NG',
        )
        
        self.framework = RegulatoryFramework.objects.create(
            code='GRI',
            name='Global Reporting Initiative',
            jurisdiction='INTERNATIONAL',
        )
        
        today = date.today()
        self.period = ReportingPeriod.objects.create(
            organization=self.org,
            name='2026 Annual',
            period_type='ANNUAL',
            start_date=today - timedelta(days=365),
            end_date=today,
        )
        
        # Create readiness
        self.readiness = FrameworkReadiness.objects.create(
            organization=self.org,
            framework=self.framework,
            reporting_period=self.period,
            total_requirements=100,
            covered_requirements=62,
            coverage_percent=62.0,
            readiness_score=62.0,
            risk_level='medium',
        )
    
    def test_get_framework_report(self):
        """Test framework report generation."""
        report = get_framework_report(self.org, self.framework)
        
        self.assertIsNotNone(report)
        self.assertEqual(report['framework'], 'GRI')
        self.assertEqual(report['organization'], 'Test Org')
        self.assertEqual(report['readiness']['coverage_percent'], 62.0)
        self.assertEqual(report['readiness']['risk_level'], 'medium')
        self.assertEqual(report['summary']['compliance_status'], 'SUBSTANTIALLY_COMPLIANT')


class GapReportTestCase(TestCase):
    """Test gap report generation."""
    
    def setUp(self):
        """Set up test data."""
        self.org = Organization.objects.create(
            name='Test Org',
            sector='finance',
            country='NG',
        )
        
        self.framework = RegulatoryFramework.objects.create(
            code='GRI',
            name='Global Reporting Initiative',
            jurisdiction='INTERNATIONAL',
        )
        
        # Create a requirement for testing
        self.requirement = FrameworkRequirement.objects.create(
            framework=self.framework,
            title='Environmental Management',
            code='ENV001',
            pillar=FrameworkRequirement.Pillar.ENVIRONMENTAL,
        )
    
    def test_get_gap_report(self):
        """Test gap report generation."""
        # Create a second requirement for testing
        requirement2 = FrameworkRequirement.objects.create(
            framework=self.framework,
            title='Labor Management',
            code='SOC001',
            pillar=FrameworkRequirement.Pillar.SOCIAL,
        )
        
        # Create gaps
        gap1 = ComplianceGapPriority.objects.create(
            organization=self.org,
            requirement=self.requirement,
            framework=self.framework,
            gap_description='Missing emissions data',
            priority_level=ComplianceGapPriority.PriorityLevel.HIGH,
            priority_score=85.0,
            is_active=True,
            efforts_to_close='Implement emissions monitoring system',
        )
        
        gap2 = ComplianceGapPriority.objects.create(
            organization=self.org,
            requirement=requirement2,
            framework=self.framework,
            gap_description='Non-compliant reporting',
            priority_level=ComplianceGapPriority.PriorityLevel.MEDIUM,
            priority_score=60.0,
            is_active=True,
            efforts_to_close='Update reporting procedures',
        )
        
        report = get_gap_report(self.org)
        
        self.assertIsNotNone(report)
        self.assertEqual(report['organization'], 'Test Org')
        self.assertEqual(report['total_gaps'], 2)
        self.assertEqual(report['gaps_by_priority']['high'], 1)
        self.assertEqual(report['gaps_by_priority']['medium'], 1)
        self.assertGreater(report['summary']['total_gaps'], 0)


class ReportGenerationTestCase(TestCase):
    """Test report generation and database storage."""
    
    def setUp(self):
        """Set up test data."""
        self.org = Organization.objects.create(
            name='Test Org',
            sector='manufacturing',
            country='NG',
        )
        
        today = date.today()
        self.period = ReportingPeriod.objects.create(
            organization=self.org,
            name='2026 Annual',
            period_type='ANNUAL',
            start_date=today - timedelta(days=365),
            end_date=today,
        )
        
        # Create ESG score
        ESGScore.objects.create(
            organization=self.org,
            reporting_period=self.period,
            environmental_score=40.0,
            social_score=45.0,
            governance_score=42.0,
            overall_score=42.3,
        )
    
    def test_generate_esg_summary_report(self):
        """Test generating and storing ESG summary report."""
        report = generate_report(
            organization=self.org,
            report_type=Report.ReportType.ESG_SUMMARY,
            reporting_period=self.period,
        )
        
        self.assertIsNotNone(report)
        self.assertEqual(report.report_type, Report.ReportType.ESG_SUMMARY)
        self.assertEqual(report.status, Report.Status.COMPLETED)
        self.assertEqual(report.organization, self.org)
        # Check that summary contains the nested summary dict with overall_esg_rating
        self.assertIn('summary', report.summary)
        self.assertIn('overall_esg_rating', report.summary.get('summary', {}))


class PartnerReportTestCase(TestCase):
    """Test partner-specific report formatting."""
    
    def setUp(self):
        """Set up test data."""
        self.org = Organization.objects.create(
            name='Test Org',
            sector='manufacturing',
            country='NG',
        )
        
        today = date.today()
        self.period = ReportingPeriod.objects.create(
            organization=self.org,
            name='2026 Annual',
            period_type='ANNUAL',
            start_date=today - timedelta(days=365),
            end_date=today,
        )
        
        # Create ESG score
        ESGScore.objects.create(
            organization=self.org,
            reporting_period=self.period,
            environmental_score=40.0,
            social_score=45.0,
            governance_score=42.0,
            overall_score=42.3,
        )
    
    def test_deg_partner_report(self):
        """Test DEG partner report format."""
        report = get_partner_report(self.org, partner_type='deg')
        
        self.assertEqual(report['report_type'], 'DEG')
        self.assertIn('environmental_impact', report)
        self.assertIn('social_impact', report)
        self.assertEqual(report['environmental_impact']['score'], 40.0)
        self.assertEqual(report['social_impact']['score'], 45.0)
    
    def test_gcf_partner_report(self):
        """Test GCF (Green Climate Fund) partner report format."""
        report = get_partner_report(self.org, partner_type='gcf')
        
        self.assertEqual(report['report_type'], 'GCF')
        self.assertIn('climate_action', report)
        self.assertEqual(report['climate_action']['environmental_score'], 40.0)
