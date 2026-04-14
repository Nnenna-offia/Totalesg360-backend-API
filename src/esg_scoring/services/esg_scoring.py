"""ESG Score Calculation Service - top-level ESG score aggregation."""
from django.db.models import Avg
from django.db import transaction
import logging

from organizations.models import Organization
from submissions.models import ReportingPeriod
from esg_scoring.models import ESGScore, PillarScore
from esg_scoring.services.pillar_scoring import calculate_all_pillar_scores

logger = logging.getLogger(__name__)


@transaction.atomic
def calculate_esg_score(
    organization: Organization,
    reporting_period: ReportingPeriod,
    weights: dict = None,
    is_consolidated: bool = False
) -> ESGScore:
    """
    Calculate overall ESG score for an organization.
    
    Logic:
    1. Ensure all 3 pillar scores exist (calculate if missing)
    2. Retrieve pillar scores
    3. Apply weighted averaging:
       overall_score = (environmental * e_weight) + (social * s_weight) + (governance * g_weight)
    4. Store ESGScore with configurable weights
    
    Score Status:
    - ACHIEVED: 76-100 (excellent performance)
    - ON_TRACK: 51-75 (good progress)
    - AT_RISK: 26-50 (needs improvement)
    - POOR: 0-25 (critical issues)
    
    Args:
        organization: Organization to score
        reporting_period: Reporting period
        weights: Dict with 'environmental', 'social', 'governance' weights
        is_consolidated: True for group scores, False for org scores
    
    Returns:
        ESGScore object
    """
    
    try:
        # Set default weights
        if weights is None:
            weights = {
                'environmental': 0.4,
                'social': 0.3,
                'governance': 0.3,
            }
        
        # Validate and normalize weights
        total_weight = sum(weights.values())
        if total_weight <= 0:
            raise ValueError("Weights must sum to positive value")
        
        # Normalize if needed
        if abs(total_weight - 1.0) > 0.01:
            logger.warning(f"Normalizing weights from {total_weight:.2f} to 1.0")
            weights = {k: v / total_weight for k, v in weights.items()}
        
        # Ensure pillar scores exist
        pillar_scores = PillarScore.objects.filter(
            organization=organization,
            reporting_period=reporting_period
        )
        
        if pillar_scores.count() < 3:
            logger.info(f"Calculating missing pillar scores for {organization.name}")
            calculate_all_pillar_scores(organization, reporting_period)
            pillar_scores = PillarScore.objects.filter(
                organization=organization,
                reporting_period=reporting_period
            )
        
        # Get pillar scores
        pillar_dict = {ps.pillar: ps.score for ps in pillar_scores}
        
        environmental_score = pillar_dict.get('environmental', 0)
        social_score = pillar_dict.get('social', 0)
        governance_score = pillar_dict.get('governance', 0)
        
        # Calculate weighted overall score
        overall_score = (
            environmental_score * weights['environmental'] +
            social_score * weights['social'] +
            governance_score * weights['governance']
        )
        
        # Clamp to 0-100
        overall_score = max(0, min(100, overall_score))
        
        # Create or update ESGScore
        esg_score, created = ESGScore.objects.update_or_create(
            organization=organization,
            reporting_period=reporting_period,
            defaults={
                'environmental_score': environmental_score,
                'social_score': social_score,
                'governance_score': governance_score,
                'overall_score': round(overall_score, 2),
                'environmental_weight': weights['environmental'],
                'social_weight': weights['social'],
                'governance_weight': weights['governance'],
                'is_consolidated': is_consolidated,
                'is_dirty': False,
            }
        )
        
        action = "Created" if created else "Updated"
        logger.info(
            f"{action} ESG score for {organization.name}: "
            f"E={environmental_score:.1f}, S={social_score:.1f}, G={governance_score:.1f}, "
            f"Overall={overall_score:.1f}"
        )
        
        return esg_score
        
    except Exception as e:
        logger.error(f"Error calculating ESG score: {str(e)}", exc_info=True)
        raise


@transaction.atomic
def calculate_esg_scores_for_all_organizations(
    reporting_period: ReportingPeriod,
    organization_ids: list = None,
    weights: dict = None
) -> list:
    """
    Calculate ESG scores for multiple organizations in batch.
    
    Args:
        reporting_period: Reporting period
        organization_ids: List of org IDs to process (if None, processes all active)
        weights: Weight configuration
    
    Returns:
        List of ESGScore objects
    """
    
    try:
        if organization_ids:
            orgs = Organization.objects.filter(id__in=organization_ids)
        else:
            orgs = Organization.objects.filter(status='ACTIVE')
        
        logger.info(f"Calculating ESG scores for {orgs.count()} organizations")
        
        scores = []
        for org in orgs:
            score = calculate_esg_score(org, reporting_period, weights=weights)
            scores.append(score)
        
        logger.info(f"Successfully calculated {len(scores)} ESG scores")
        return scores
        
    except Exception as e:
        logger.error(f"Error in batch ESG score calculation: {str(e)}", exc_info=True)
        raise


def get_esg_score_summary(
    organization: Organization,
    reporting_period: ReportingPeriod
) -> dict:
    """
    Get ESG score summary for frontend consumption.
    
    Returns dictionary with:
    - overall, environmental, social, governance scores
    - strengths (pillars >= 70)
    - weaknesses (pillars < 50)
    - ranking (E/S/G sorted by score)
    - calculated_at timestamp
    
    Args:
        organization: Organization
        reporting_period: Reporting period
    
    Returns:
        Dictionary with score summary
    """
    
    try:
        esg_score = ESGScore.objects.get(
            organization=organization,
            reporting_period=reporting_period
        )
        
        return {
            'organization_id': str(organization.id),
            'organization_name': organization.name,
            'period_id': str(reporting_period.id),
            'period_name': reporting_period.name,
            'overall': round(esg_score.overall_score, 2),
            'environmental': round(esg_score.environmental_score, 2),
            'social': round(esg_score.social_score, 2),
            'governance': round(esg_score.governance_score, 2),
            'strengths': list(esg_score.get_strengths().items()),
            'weaknesses': list(esg_score.get_weaknesses().items()),
            'ranking': esg_score.get_pillar_ranking(),
            'calculated_at': esg_score.calculated_at.isoformat(),
        }
    except ESGScore.DoesNotExist:
        logger.warning(f"No ESG score found for {organization.name} in {reporting_period.name}")
        return None
    except Exception as e:
        logger.error(f"Error retrieving ESG score summary: {str(e)}", exc_info=True)
        raise
