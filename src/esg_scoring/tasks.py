"""ESG Scoring Celery Tasks - Async score calculations."""
from celery import shared_task
import logging

logger = logging.getLogger(__name__)


# Celery tasks for async processing:
# 1. calculate_org_indicator_scores.delay(org_id, period_id)
# 2. calculate_org_pillar_scores.delay(org_id, period_id)
# 3. calculate_org_esg_score.delay(org_id, period_id)
# 4. batch_calculate_all_scores.delay(period_id)
# 5. calculate_group_consolidation.delay(group_id, period_id)

# For now, this is a placeholder. Tasks will be added in phase 2.

@shared_task(bind=True, max_retries=3)
def calculate_org_indicator_scores(self, org_id, period_id):
    """Calculate all indicator scores for an organization."""
    try:
        from organizations.models import Organization
        from submissions.models import ReportingPeriod
        from esg_scoring.services.indicator_scoring import calculate_all_indicator_scores
        
        org = Organization.objects.get(id=org_id)
        period = ReportingPeriod.objects.get(id=period_id)
        
        calculate_all_indicator_scores(org, period)
        logger.info(f"Calculated indicator scores for {org.name} in {period.name}")
        return {"status": "success", "org_id": org_id, "period_id": period_id}
    except Exception as exc:
        logger.error(f"Error calculating indicator scores: {str(exc)}", exc_info=True)
        raise


@shared_task(bind=True, max_retries=3)
def calculate_org_pillar_scores(self, org_id, period_id):
    """Calculate all pillar scores for an organization."""
    try:
        from organizations.models import Organization
        from submissions.models import ReportingPeriod
        from esg_scoring.services.pillar_scoring import calculate_all_pillar_scores
        
        org = Organization.objects.get(id=org_id)
        period = ReportingPeriod.objects.get(id=period_id)
        
        calculate_all_pillar_scores(org, period)
        logger.info(f"Calculated pillar scores for {org.name} in {period.name}")
        return {"status": "success", "org_id": org_id, "period_id": period_id}
    except Exception as exc:
        logger.error(f"Error calculating pillar scores: {str(exc)}", exc_info=True)
        raise


@shared_task(bind=True, max_retries=3)
def calculate_org_esg_score(self, org_id, period_id, weights=None):
    """Calculate ESG score for an organization."""
    try:
        from organizations.models import Organization
        from submissions.models import ReportingPeriod
        from esg_scoring.services.esg_scoring import calculate_esg_score
        
        org = Organization.objects.get(id=org_id)
        period = ReportingPeriod.objects.get(id=period_id)
        
        calculate_esg_score(org, period, weights=weights)
        logger.info(f"Calculated ESG score for {org.name} in {period.name}")
        return {"status": "success", "org_id": org_id, "period_id": period_id}
    except Exception as exc:
        logger.error(f"Error calculating ESG score: {str(exc)}", exc_info=True)
        raise


@shared_task(bind=True, max_retries=3)
def batch_calculate_all_scores(self, period_id, org_ids=None):
    """Calculate scores for all organizations in a period."""
    try:
        from submissions.models import ReportingPeriod
        from organizations.models import Organization
        from esg_scoring.services.esg_scoring import calculate_esg_scores_for_all_organizations
        
        period = ReportingPeriod.objects.get(id=period_id)
        
        if org_ids:
            orgs = Organization.objects.filter(id__in=org_ids)
        else:
            orgs = Organization.objects.filter(status='ACTIVE')
        
        org_ids_list = [org.id for org in orgs]
        calculate_esg_scores_for_all_organizations(period, org_ids=org_ids_list)
        
        logger.info(f"Calculated scores for {len(org_ids_list)} organizations in {period.name}")
        return {"status": "success", "period_id": period_id, "org_count": len(org_ids_list)}
    except Exception as exc:
        logger.error(f"Error batch calculating scores: {str(exc)}", exc_info=True)
        raise


@shared_task(bind=True, max_retries=3)
def calculate_group_consolidation(self, group_id, period_id):
    """Calculate consolidated group score."""
    try:
        from organizations.models import Organization
        from submissions.models import ReportingPeriod
        from esg_scoring.selectors.group_scoring import calculate_group_esg_score
        
        group = Organization.objects.get(id=group_id)
        period = ReportingPeriod.objects.get(id=period_id)
        
        calculate_group_esg_score(group, period)
        logger.info(f"Calculated group consolidation for {group.name} in {period.name}")
        return {"status": "success", "group_id": group_id, "period_id": period_id}
    except Exception as exc:
        logger.error(f"Error calculating group consolidation: {str(exc)}", exc_info=True)
        raise
