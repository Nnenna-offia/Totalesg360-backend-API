"""ESG Score Trends and Historical Analysis."""
from django.db.models import Avg
import logging

from organizations.models import Organization
from submissions.models import ReportingPeriod
from esg_scoring.models import ESGScore, IndicatorScore, PillarScore

logger = logging.getLogger(__name__)


def get_esg_score_trend(
    organization: Organization,
    periods: int = 12
) -> dict:
    """Get ESG score trend over last N reporting periods."""

    try:
        esg_scores = ESGScore.objects.filter(
            organization=organization
        ).order_by('-reporting_period__end_date')[:periods]

        if not esg_scores:
            return {
                "organization": str(organization.id),
                "name": organization.name,
                "trend": [],
                "has_data": False,
            }

        trend_data = [
            {
                "period": score.reporting_period.name,
                "overall": round(score.overall_score, 2),
                "environmental": round(score.environmental_score, 2),
                "social": round(score.social_score, 2),
                "governance": round(score.governance_score, 2),
            }
            for score in reversed(esg_scores)
        ]

        overall_scores = [s["overall"] for s in trend_data]

        return {
            "organization": str(organization.id),
            "name": organization.name,
            "trend": trend_data,
            "has_data": True,
            "statistics": {
                "latest_score": overall_scores[-1] if overall_scores else 0,
                "average_score": round(sum(overall_scores) / len(overall_scores), 2),
            }
        }
    except Exception as e:
        logger.error(f"Error retrieving ESG trend: {str(e)}", exc_info=True)
        return None


def get_pillar_trend(
    organization: Organization,
    pillar: str,
    periods: int = 12
) -> dict:
    """Get trend for specific pillar (Environmental/Social/Governance)."""

    try:
        pillar_scores = PillarScore.objects.filter(
            organization=organization,
            pillar=pillar
        ).order_by('-reporting_period__end_date')[:periods]

        trend_data = [
            {
                "period": score.reporting_period.name,
                "score": round(score.score, 2),
            }
            for score in reversed(pillar_scores)
        ]

        scores = [s["score"] for s in trend_data]

        return {
            "organization": str(organization.id),
            "pillar": pillar,
            "trend": trend_data,
            "latest": scores[-1] if scores else 0,
        }
    except Exception as e:
        logger.error(f"Error retrieving pillar trend: {str(e)}", exc_info=True)
        return None


def get_year_over_year_comparison(
    organization: Organization,
    periods: int = 4
) -> dict:
    """Compare ESG scores year-over-year."""

    try:
        esg_scores = ESGScore.objects.filter(
            organization=organization
        ).order_by('-reporting_period__end_date')[:periods]

        scores_list = list(reversed(esg_scores))

        if len(scores_list) < 2:
            return {"has_comparison": False}

        latest = scores_list[-1]
        previous = scores_list[-2]

        return {
            "organization": str(organization.id),
            "has_comparison": True,
            "latest_period": latest.reporting_period.name,
            "change": round(latest.overall_score - previous.overall_score, 2),
        }
    except Exception as e:
        logger.error(f"Error calculating YoY comparison: {str(e)}", exc_info=True)
        return None
