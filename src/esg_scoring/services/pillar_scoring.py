"""Pillar Scoring Service - aggregates indicator scores into pillar scores."""
from django.db.models import Avg
from django.db import transaction
import logging

from organizations.models import Organization
from indicators.models import Indicator
from submissions.models import ReportingPeriod
from esg_scoring.models import IndicatorScore, PillarScore

logger = logging.getLogger(__name__)


@transaction.atomic
def calculate_pillar_score(
    organization: Organization,
    pillar: str,
    reporting_period: ReportingPeriod
) -> PillarScore:
    """
    Calculate score for a pillar (Environmental/Social/Governance).

    Logic:
    1. Get all indicators under this pillar
    2. Get corresponding indicator scores
    3. Average the indicator scores
    4. Count on-track and at-risk indicators
    5. Store pillar score

    Args:
        organization: Organization
        pillar: Pillar name (ENVIRONMENTAL, SOCIAL, GOVERNANCE)
        reporting_period: Reporting period

    Returns:
        PillarScore object
    """

    try:
        # Get indicators for this pillar
        indicators = Indicator.objects.filter(
            pillar=pillar,
            is_active=True
        )

        if not indicators.exists():
            logger.warning(f"No active indicators found for pillar {pillar}")
            return None

        # Get indicator scores
        indicator_scores = IndicatorScore.objects.filter(
            organization=organization,
            indicator__in=indicators,
            reporting_period=reporting_period
        )

        if not indicator_scores.exists():
            logger.warning(
                f"No indicator scores found for {pillar} in {organization.name}"
            )
            score = 0
            on_track_count = 0
            at_risk_count = 0
        else:
            # Average score
            avg_result = indicator_scores.aggregate(Avg('score'))
            score = avg_result['score__avg'] or 0

            # Count status
            on_track_count = indicator_scores.filter(
                status__in=[IndicatorScore.Status.ON_TRACK, IndicatorScore.Status.ACHIEVED]
            ).count()

            at_risk_count = indicator_scores.filter(
                status__in=[IndicatorScore.Status.AT_RISK, IndicatorScore.Status.POOR]
            ).count()

        # Create or update pillar score
        pillar_score, created = PillarScore.objects.update_or_create(
            organization=organization,
            pillar=pillar,
            reporting_period=reporting_period,
            defaults={
                'score': round(score, 2),
                'indicator_count': indicator_scores.count(),
                'on_track_count': on_track_count,
                'at_risk_count': at_risk_count,
                'is_dirty': False,
            }
        )

        action = "Created" if created else "Updated"
        logger.info(
            f"{action} {pillar} pillar score for {organization.name}: "
            f"{score:.1f} ({indicator_scores.count()} indicators)"
        )

        return pillar_score

    except Exception as e:
        logger.error(f"Error calculating pillar score: {str(e)}", exc_info=True)
        raise


@transaction.atomic
def calculate_all_pillar_scores(
    organization: Organization,
    reporting_period: ReportingPeriod
) -> dict:
    """
    Calculate all 3 pillar scores (E/S/G) for an organization.

    Args:
        organization: Organization
        reporting_period: Reporting period

    Returns:
        Dict with pillar_type: PillarScore
    """

    try:
        pillar_types = [
            PillarScore.PillarType.ENVIRONMENTAL,
            PillarScore.PillarType.SOCIAL,
            PillarScore.PillarType.GOVERNANCE,
        ]

        pillar_scores = {}

        for pillar in pillar_types:
            score = calculate_pillar_score(organization, pillar, reporting_period)
            if score:
                pillar_scores[pillar] = score

        logger.info(f"Calculated {len(pillar_scores)} pillar scores for {organization.name}")
        return pillar_scores

    except Exception as e:
        logger.error(f"Error calculating all pillar scores: {str(e)}", exc_info=True)
        raise


def get_pillar_scores_dict(
    organization: Organization,
    reporting_period: ReportingPeriod
) -> dict:
    """
    Get pillar scores as simple dict: {pillar_name: score_value}.

    Args:
        organization: Organization
        reporting_period: Reporting period

    Returns:
        Dict like {'environmental': 42.5, 'social': 38.2, 'governance': 51.0}
    """

    try:
        billar_scores = PillarScore.objects.filter(
            organization=organization,
            reporting_period=reporting_period
        )

        scores_dict = {
            score.pillar: round(score.score, 2)
            for score in pillar_scores
        }

        return scores_dict

    except Exception as e:
        logger.error(f"Error retrieving pillar scores dict: {str(e)}", exc_info=True)
        return {}
