"""Cache management services for group aggregations."""
from typing import Optional
from django.core.cache import cache
from organizations.models import Organization
from submissions.models import ReportingPeriod


# Cache key prefixes
GROUP_DASHBOARD_CACHE_KEY = "group_dashboard_{org_id}_{period_id}"
GROUP_READINESS_CACHE_KEY = "group_readiness_{org_id}_{period_id}"
GROUP_GAPS_CACHE_KEY = "group_gaps_{org_id}"
GROUP_RECOMMENDATIONS_CACHE_KEY = "group_recommendations_{org_id}"
GROUP_ESG_SCORE_CACHE_KEY = "group_esg_score_{org_id}_{period_id}"
SUBSIDIARY_RANKING_CACHE_KEY = "subsidiary_ranking_{org_id}_{period_id}"


# Cache TTL (in seconds)
CACHE_TTL_DEFAULT = 3600  # 1 hour
CACHE_TTL_DASHBOARD = 1800  # 30 minutes (more frequently accessed)
CACHE_TTL_GAPS = 7200  # 2 hours (less frequently changes)


def get_cache_key_for_group_dashboard(
    org: Organization,
    period: Optional[ReportingPeriod] = None,
) -> str:
    """Get cache key for group dashboard."""
    period_id = period.id if period else 'latest'
    return GROUP_DASHBOARD_CACHE_KEY.format(org_id=org.id, period_id=period_id)


def get_cache_key_for_readiness(
    org: Organization,
    period: Optional[ReportingPeriod] = None,
) -> str:
    """Get cache key for group readiness."""
    period_id = period.id if period else 'latest'
    return GROUP_READINESS_CACHE_KEY.format(org_id=org.id, period_id=period_id)


def get_cache_key_for_gaps(org: Organization) -> str:
    """Get cache key for group gaps."""
    return GROUP_GAPS_CACHE_KEY.format(org_id=org.id)


def get_cache_key_for_recommendations(org: Organization) -> str:
    """Get cache key for group recommendations."""
    return GROUP_RECOMMENDATIONS_CACHE_KEY.format(org_id=org.id)


def get_cache_key_for_esg_score(
    org: Organization,
    period: Optional[ReportingPeriod] = None,
) -> str:
    """Get cache key for group ESG score."""
    period_id = period.id if period else 'latest'
    return GROUP_ESG_SCORE_CACHE_KEY.format(org_id=org.id, period_id=period_id)


def get_cache_key_for_ranking(
    org: Organization,
    period: Optional[ReportingPeriod] = None,
) -> str:
    """Get cache key for subsidiary ranking."""
    period_id = period.id if period else 'latest'
    return SUBSIDIARY_RANKING_CACHE_KEY.format(org_id=org.id, period_id=period_id)


def invalidate_group_cache(org: Organization, period: Optional[ReportingPeriod] = None) -> None:
    """
    Invalidate all caches for a group organization.
    
    Called when any data affecting group aggregation changes.
    """
    # Invalidate all period-specific caches
    cache.delete(get_cache_key_for_group_dashboard(org, period))
    cache.delete(get_cache_key_for_readiness(org, period))
    cache.delete(get_cache_key_for_esg_score(org, period))
    cache.delete(get_cache_key_for_ranking(org, period))
    
    # Invalidate period-independent caches
    cache.delete(get_cache_key_for_gaps(org))
    cache.delete(get_cache_key_for_recommendations(org))
    
    # If no specific period, invalidate latest period caches too
    if not period:
        cache.delete(get_cache_key_for_group_dashboard(org))
        cache.delete(get_cache_key_for_readiness(org))
        cache.delete(get_cache_key_for_esg_score(org))
        cache.delete(get_cache_key_for_ranking(org))


def invalidate_parent_cache(org: Organization, period: Optional[ReportingPeriod] = None) -> None:
    """
    Invalidate cache for parent organization when a subsidiary changes.
    
    Called when subsidiary data is updated.
    """
    if org.parent:
        invalidate_group_cache(org.parent, period)


def set_dashboard_cache(
    org: Organization,
    data: dict,
    period: Optional[ReportingPeriod] = None,
) -> None:
    """Cache group dashboard data."""
    key = get_cache_key_for_group_dashboard(org, period)
    cache.set(key, data, CACHE_TTL_DASHBOARD)


def set_readiness_cache(
    org: Organization,
    data: dict,
    period: Optional[ReportingPeriod] = None,
) -> None:
    """Cache group readiness data."""
    key = get_cache_key_for_readiness(org, period)
    cache.set(key, data, CACHE_TTL_DEFAULT)


def set_gaps_cache(org: Organization, data: list) -> None:
    """Cache group gaps data."""
    key = get_cache_key_for_gaps(org)
    cache.set(key, data, CACHE_TTL_GAPS)


def set_recommendations_cache(org: Organization, data: list) -> None:
    """Cache group recommendations data."""
    key = get_cache_key_for_recommendations(org)
    cache.set(key, data, CACHE_TTL_DEFAULT)


def set_esg_score_cache(
    org: Organization,
    data: dict,
    period: Optional[ReportingPeriod] = None,
) -> None:
    """Cache group ESG score data."""
    key = get_cache_key_for_esg_score(org, period)
    cache.set(key, data, CACHE_TTL_DEFAULT)


def set_ranking_cache(
    org: Organization,
    data: list,
    period: Optional[ReportingPeriod] = None,
) -> None:
    """Cache subsidiary ranking data."""
    key = get_cache_key_for_ranking(org, period)
    cache.set(key, data, CACHE_TTL_DEFAULT)
