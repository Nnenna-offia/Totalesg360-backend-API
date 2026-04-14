"""Group ESG Score Calculation - consolidates scores from subsidiaries."""
from django.db.models import Avg
import logging

from organizations.models import Organization
from submissions.models import ReportingPeriod
from organizations.selectors.organization_hierarchy import get_organization_descendants
from esg_scoring.models import ESGScore
from esg_scoring.services.esg_scoring import calculate_esg_score

logger = logging.getLogger(__name__)


def calculate_group_esg_score(
    parent_organization: Organization,
    reporting_period: ReportingPeriod,
    weights: dict = None,
    include_parent: bool = False
) -> ESGScore:
    """
    Calculate consolidated ESG score for a group/parent organization.

    Aggregates scores from all subsidiaries using weighted average.

    Args:
        parent_organization: Parent/group organization
        reporting_period: Reporting period
        weights: Weight config for pillar scoring
        include_parent: Whether to include parent org's own score

    Returns:
        ESGScore object marked as consolidated=True
    """

    try:
        # Get all descendants
        descendants = get_organization_descendants(
            parent_organization,
            include_self=include_parent
        )

        if not descendants:
            descendants = [parent_organization]

        # Get ESG scores for all descendants
        esg_scores = ESGScore.objects.filter(
            organization__in=descendants,
            reporting_period=reporting_period
        )

        if not esg_scores.exists():
            logger.warning(
                f"No ESG scores found for subsidiaries of {parent_organization.name}"
            )
            from esg_scoring.services.esg_scoring import calculate_esg_scores_for_all_organizations
            calculate_esg_scores_for_all_organizations(
                reporting_period,
                organization_ids=[d.id for d in descendants],
                weights=weights
            )
            esg_scores = ESGScore.objects.filter(
                organization__in=descendants,
                reporting_period=reporting_period
            )

        # Aggregate scores
        consolidated_environmental = esg_scores.aggregate(
            Avg('environmental_score')
        )['environmental_score__avg'] or 0

        consolidated_social = esg_scores.aggregate(
            Avg('social_score')
        )['social_score__avg'] or 0

        consolidated_governance = esg_scores.aggregate(
            Avg('governance_score')
        )['governance_score__avg'] or 0

        if weights is None:
            weights = {
                'environmental': 0.4,
                'social': 0.3,
                'governance': 0.3,
            }

        consolidated_overall = (
            consolidated_environmental * weights['environmental'] +
            consolidated_social * weights['social'] +
            consolidated_governance * weights['governance']
        )

        consolidated_overall = max(0, min(100, consolidated_overall))

        # Calculate as consolidated group score
        group_score = calculate_esg_score(
            parent_organization,
            reporting_period,
            weights=weights,
            is_consolidated=True
        )

        # Override with consolidated values
        group_score.environmental_score = consolidated_environmental
        group_score.social_score = consolidated_social
        group_score.governance_score = consolidated_governance
        group_score.overall_score = consolidated_overall
        group_score.is_consolidated = True
        group_score.save()

        logger.info(
            f"Calculated consolidated group score for {parent_organization.name}: "
            f"{consolidated_overall:.1f}"
        )

        return group_score

    except Exception as e:
        logger.error(f"Error calculating group ESG score: {str(e)}", exc_info=True)
        raise


def get_group_esg_breakdown(
    parent_organization: Organization,
    reporting_period: ReportingPeriod
) -> dict:
    """Get ESG score breakdown for a group showing performance by subsidiary."""

    try:
        group_score = ESGScore.objects.get(
            organization=parent_organization,
            reporting_period=reporting_period,
            is_consolidated=True
        )

        descendants = get_organization_descendants(parent_organization, include_self=False)
        subsidiary_scores = ESGScore.objects.filter(
            organization__in=descendants,
            reporting_period=reporting_period
        ).values('organization__name', 'organization__id', 'overall_score', 'environmental_score', 'social_score', 'governance_score')

        return {
            "group": {
                "overall": group_score.overall_score,
                "environmental": group_score.environmental_score,
                "social": group_score.social_score,
                "governance": group_score.governance_score,
            },
            "subsidiaries": list(subsidiary_scores),
            "subsidiary_count": len(list(subsidiary_scores)),
            "calculated_at": group_score.calculated_at,
        }
    except ESGScore.DoesNotExist:
        logger.warning(
            f"No consolidated group score found for {parent_organization.name}"
        )
        return None


def get_top_performing_subsidiaries(
    parent_organization: Organization,
    reporting_period: ReportingPeriod,
    limit: int = 5
) -> list:
    """Get top performing subsidiaries by ESG score."""

    descendants = get_organization_descendants(parent_organization, include_self=False)
    subsidiary_scores = ESGScore.objects.filter(
        organization__in=descendants,
        reporting_period=reporting_period
    ).order_by('-overall_score')[:limit]

    return [
        {
            "organization": str(score.organization.id),
            "name": score.organization.name,
            "overall_score": score.overall_score,
            "environmental": score.environmental_score,
            "social": score.social_score,
            "governance": score.governance_score,
        }
        for score in subsidiary_scores
    ]
