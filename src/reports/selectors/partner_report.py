"""Partner Report Selector - generates partner-specific report formats."""
from typing import Dict, Any

from organizations.models import Organization
from reports.selectors.esg_summary import get_esg_summary_report
from reports.selectors.framework_report import get_framework_report


def get_partner_report(
    organization: Organization,
    partner_type: str = "deg",
) -> Dict[str, Any]:
    """
    Get partner-specific ESG/compliance report.
    
    Supports:
    - DEG: Focus on environmental + social impact
    - USAID: Focus on development outcomes + environmental
    - GCF: Focus on climate outcomes (environmental)
    - FRC: Focus on recovery + climate
    
    Args:
        organization: Organization to report on
        partner_type: Partner type (deg, usaid, gcf, frc)
    
    Returns:
        Dictionary with partner report formatted for stakeholder needs
    """
    # Get base ESG summary
    esg_summary = get_esg_summary_report(organization)
    
    if partner_type.lower() == "deg":
        return _format_deg_report(organization, esg_summary)
    elif partner_type.lower() == "usaid":
        return _format_usaid_report(organization, esg_summary)
    elif partner_type.lower() == "gcf":
        return _format_gcf_report(organization, esg_summary)
    elif partner_type.lower() == "frc":
        return _format_frc_report(organization, esg_summary)
    else:
        return esg_summary


def _format_deg_report(organization: Organization, esg_summary: Dict[str, Any]) -> Dict[str, Any]:
    """
    DEG (Deutsche Entwicklungsgesellschaft) report format.
    Focus: Environmental & Social Impact, Development Outcomes
    """
    return {
        "report_type": "DEG",
        "partner": "Deutsche Entwicklungsgesellschaft",
        "organization": organization.name,
        "organization_id": str(organization.id),
        "reporting_period": esg_summary.get("reporting_period"),
        "environmental_impact": {
            "score": esg_summary.get("esg_score", {}).get("environmental"),
            "assessment": _score_to_assessment(esg_summary.get("esg_score", {}).get("environmental")),
            "key_areas": [
                {"requirement": gap.get("requirement"), "priority": gap.get("priority")}
                for gap in esg_summary.get("compliance_gaps", [])
                if "environmental" in gap.get("requirement", "").lower() or
                   "emission" in gap.get("requirement", "").lower() or
                   "energy" in gap.get("requirement", "").lower()
            ][:5],
        },
        "social_impact": {
            "score": esg_summary.get("esg_score", {}).get("social"),
            "assessment": _score_to_assessment(esg_summary.get("esg_score", {}).get("social")),
            "key_areas": [
                {"requirement": gap.get("requirement"), "priority": gap.get("priority")}
                for gap in esg_summary.get("compliance_gaps", [])
                if "social" in gap.get("requirement", "").lower() or
                   "labor" in gap.get("requirement", "").lower() or
                   "community" in gap.get("requirement", "").lower()
            ][:5],
        },
        "priority_actions": esg_summary.get("recommendations", [])[:5],
        "summary": {
            "overall_readiness": esg_summary.get("summary", {}).get("overall_esg_rating"),
            "critical_issues": esg_summary.get("summary", {}).get("critical_gaps"),
            "implementation_status": "In Progress",
        }
    }


def _format_usaid_report(organization: Organization, esg_summary: Dict[str, Any]) -> Dict[str, Any]:
    """
    USAID report format.
    Focus: Development Outcomes, Environmental Sustainability, Social Progress
    """
    return {
        "report_type": "USAID",
        "partner": "United States Agency for International Development",
        "organization": organization.name,
        "organization_id": str(organization.id),
        "reporting_period": esg_summary.get("reporting_period"),
        "development_outcomes": {
            "social_score": esg_summary.get("esg_score", {}).get("social"),
            "environmental_score": esg_summary.get("esg_score", {}).get("environmental"),
            "combined_score": (
                (esg_summary.get("esg_score", {}).get("social", 0) +
                 esg_summary.get("esg_score", {}).get("environmental", 0)) / 2
            ),
            "assessment": _score_to_assessment(
                (esg_summary.get("esg_score", {}).get("social", 0) +
                 esg_summary.get("esg_score", {}).get("environmental", 0)) / 2
            ),
        },
        "sustainability_framework": esg_summary.get("framework_readiness", [])[:5],
        "risks_and_gaps": esg_summary.get("compliance_gaps", [])[:8],
        "capacity_development": esg_summary.get("recommendations", [])[:5],
        "summary": {
            "development_impact_level": esg_summary.get("summary", {}).get("overall_esg_rating"),
            "key_challenges": esg_summary.get("summary", {}).get("critical_gaps"),
            "resource_needs": "To be determined",
        }
    }


def _format_gcf_report(organization: Organization, esg_summary: Dict[str, Any]) -> Dict[str, Any]:
    """
    GCF (Green Climate Fund) report format.
    Focus: Climate Action, Environmental Sustainability
    """
    return {
        "report_type": "GCF",
        "partner": "Green Climate Fund",
        "organization": organization.name,
        "organization_id": str(organization.id),
        "reporting_period": esg_summary.get("reporting_period"),
        "climate_action": {
            "environmental_score": esg_summary.get("esg_score", {}).get("environmental"),
            "assessment": _score_to_assessment(esg_summary.get("esg_score", {}).get("environmental")),
        },
        "climate_related_gaps": [
            gap for gap in esg_summary.get("compliance_gaps", [])
            if any(keyword in gap.get("requirement", "").lower() 
                   for keyword in ["climate", "greenhouse", "emission", "carbon", "renewable", "energy"])
        ][:8],
        "emissions_management": {
            "framework_readiness": esg_summary.get("framework_readiness", []),
            "mitigation_actions": esg_summary.get("recommendations", [])[:5],
        },
        "summary": {
            "climate_commitment_level": esg_summary.get("summary", {}).get("overall_esg_rating"),
            "climate_readiness": _map_rating_to_readiness(esg_summary.get("summary", {}).get("overall_esg_rating")),
            "investment_readiness": "To be assessed",
        }
    }


def _format_frc_report(organization: Organization, esg_summary: Dict[str, Any]) -> Dict[str, Any]:
    """
    FRC (Facility for Recovery and Climate) report format.
    Focus: Climate Resilience, Recovery, Environmental Management
    """
    return {
        "report_type": "FRC",
        "partner": "Facility for Recovery and Climate",
        "organization": organization.name,
        "organization_id": str(organization.id),
        "reporting_period": esg_summary.get("reporting_period"),
        "recovery_framework": {
            "environmental_score": esg_summary.get("esg_score", {}).get("environmental"),
            "social_score": esg_summary.get("esg_score", {}).get("social"),
            "governance_score": esg_summary.get("esg_score", {}).get("governance"),
            "combined": esg_summary.get("esg_score", {}).get("overall"),
        },
        "climate_resilience": [
            gap for gap in esg_summary.get("compliance_gaps", [])
            if any(keyword in gap.get("requirement", "").lower() 
                   for keyword in ["resilience", "adaptation", "risk", "recovery", "climate"])
        ][:8],
        "recovery_actions": esg_summary.get("recommendations", [])[:5],
        "summary": {
            "recovery_readiness": _calculate_recovery_readiness(esg_summary),
            "climate_adaptation_capacity": _score_to_assessment(
                esg_summary.get("esg_score", {}).get("environmental")
            ),
            "next_steps": "Detailed assessment required",
        }
    }


def _score_to_assessment(score: float) -> str:
    """Convert numeric score to assessment text."""
    if not score:
        return "No Data"
    
    if score >= 80:
        return "Excellent"
    elif score >= 60:
        return "Good"
    elif score >= 40:
        return "Moderate"
    elif score >= 20:
        return "Weak"
    else:
        return "Critical"


def _map_rating_to_readiness(rating: str) -> str:
    """Map ESG rating to investment readiness."""
    mapping = {
        "EXCELLENT": "Highly Ready",
        "GOOD": "Ready",
        "MODERATE": "Conditionally Ready",
        "WEAK": "Needs Development",
        "CRITICAL": "Not Ready",
        "UNKNOWN": "Assessment Required",
    }
    return mapping.get(rating, "Assessment Required")


def _calculate_recovery_readiness(esg_summary: Dict[str, Any]) -> str:
    """Calculate recovery readiness score."""
    esg_score = esg_summary.get("esg_score")
    if not esg_score:
        return "Unknown"
    
    avg = (
        (esg_score.get("environmental") or 0) +
        (esg_score.get("social") or 0) +
        (esg_score.get("governance") or 0)
    ) / 3
    
    if avg >= 75:
        return "Highly Ready"
    elif avg >= 55:
        return "Ready"
    elif avg >= 35:
        return "Moderately Ready"
    else:
        return "Needs Support"
