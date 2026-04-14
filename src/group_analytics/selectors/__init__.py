"""Group Analytics selectors for aggregation queries."""

from .group_readiness import (
    get_group_framework_readiness,
    get_group_readiness_summary,
)
from .group_gaps import (
    get_group_top_gaps,
    get_group_gap_summary,
)
from .group_recommendations import (
    get_group_recommendations,
    get_group_recommendations_summary,
)
from .group_scoring import (
    calculate_group_esg_score,
    get_subsidiary_ranking,
    get_group_esg_trend,
)
from .group_dashboard import (
    get_group_dashboard,
    get_subsidiary_comparison,
    get_group_portfolio_summary,
)

__all__ = [
    # Readiness
    'get_group_framework_readiness',
    'get_group_readiness_summary',
    # Gaps
    'get_group_top_gaps',
    'get_group_gap_summary',
    # Recommendations
    'get_group_recommendations',
    'get_group_recommendations_summary',
    # Scoring
    'calculate_group_esg_score',
    'get_subsidiary_ranking',
    'get_group_esg_trend',
    # Dashboard
    'get_group_dashboard',
    'get_subsidiary_comparison',
    'get_group_portfolio_summary',
]
