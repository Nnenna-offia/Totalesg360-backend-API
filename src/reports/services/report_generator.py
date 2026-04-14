"""Report Generator Service - generates and stores reports."""
import json
from typing import Dict, Any, Optional
from datetime import timedelta

from django.utils import timezone
from django.db import transaction

from organizations.models import Organization, RegulatoryFramework
from submissions.models import ReportingPeriod
from reports.models import Report
from reports.selectors import (
    get_esg_summary_report,
    get_framework_report,
    get_group_esg_report,
    get_gap_report,
    get_partner_report,
)


@transaction.atomic
def generate_report(
    organization: Organization,
    report_type: str,
    reporting_period: Optional[ReportingPeriod] = None,
    framework: Optional[RegulatoryFramework] = None,
    partner_type: str = "none",
    generated_by=None,
    file_format: str = "json",
) -> Report:
    """
    Generate and store a report.
    
    Aggregates data from appropriate selectors based on report type:
    - ESG_SUMMARY: Uses esg_summary selector
    - FRAMEWORK: Uses framework_report selector
    - GROUP: Uses group_report selector
    - GAP: Uses gap_report selector
    - PARTNER: Uses partner_report selector
    
    Args:
        organization: Organization for report
        report_type: Type of report (esg_summary, framework, group, gap, partner)
        reporting_period: Optional reporting period
        framework: Required for framework reports
        partner_type: Partner type (deg, usaid, gcf, frc)
        generated_by: User who requested report
        file_format: Export format (json, pdf, csv, html)
    
    Returns:
        Report database instance
    """
    # Mark as generating
    report = Report.objects.create(
        organization=organization,
        report_type=report_type,
        framework=framework,
        partner_type=partner_type,
        reporting_period_id=reporting_period.id if reporting_period else None,
        generated_by=generated_by,
        status=Report.Status.GENERATING,
        file_format=file_format,
    )
    
    try:
        # Generate report data based on type
        if report_type == Report.ReportType.ESG_SUMMARY:
            report_data = get_esg_summary_report(organization, reporting_period)
        
        elif report_type == Report.ReportType.FRAMEWORK:
            if not framework:
                raise ValueError("Framework is required for framework reports")
            report_data = get_framework_report(organization, framework)
        
        elif report_type == Report.ReportType.GROUP:
            if organization.organization_type != Organization.OrganizationType.GROUP:
                raise ValueError("Organization must be a group")
            report_data = get_group_esg_report(organization, reporting_period)
        
        elif report_type == Report.ReportType.GAP:
            report_data = get_gap_report(organization)
        
        elif report_type == Report.ReportType.PARTNER:
            report_data = get_partner_report(organization, partner_type)
        
        else:
            raise ValueError(f"Unknown report type: {report_type}")
        
        # Extract summary data for quick access
        summary = _extract_summary(report_data)
        
        # Store report
        report.summary = summary
        report.metadata = {
            "report_type": report_type,
            "framework": framework.code if framework else None,
            "partner_type": partner_type,
            "generated_period": reporting_period.name if reporting_period else None,
        }
        report.status = Report.Status.COMPLETED
        report.expires_at = timezone.now() + timedelta(hours=1)  # Cache for 1 hour
        report.save()
        
        return report
    
    except Exception as e:
        report.status = Report.Status.FAILED
        report.metadata = {"error": str(e)}
        report.save()
        raise


def regenerate_all_reports(organization: Organization) -> int:
    """
    Regenerate all reports for an organization (called on data changes).
    
    Args:
        organization: Organization to regenerate reports for
    
    Returns:
        Count of reports regenerated
    """
    count = 0
    
    # Get all active reports for this organization
    reports = Report.objects.filter(
        organization=organization,
        status=Report.Status.COMPLETED,
    )
    
    for report in reports:
        try:
            generate_report(
                organization=organization,
                report_type=report.report_type,
                reporting_period_id=report.reporting_period_id,
                framework=report.framework,
                partner_type=report.partner_type,
                generated_by=report.generated_by,
                file_format=report.file_format,
            )
            count += 1
        except Exception as e:
            print(f"Error regenerating report {report.id}: {e}")
    
    return count


def _extract_summary(report_data: Dict[str, Any]) -> Dict[str, Any]:
    """Extract key summary metrics from full report."""
    return {
        "organization": report_data.get("organization"),
        "reporting_period": report_data.get("reporting_period"),
        "summary": report_data.get("summary", {}),
        "generation_timestamp": timezone.now().isoformat(),
    }
