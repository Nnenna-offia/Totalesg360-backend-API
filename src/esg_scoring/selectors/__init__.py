"""ESG Scoring Selectors - Read-only queries for scores and analysis."""

from esg_scoring.selectors.group_scoring import (
    calculate_group_esg_score,
    get_group_esg_breakdown,
    get_top_performing_subsidiaries,
)

from esg_scoring.selectors.trends import (
    get_esg_score_trend,
    get_pillar_trend,
    get_year_over_year_comparison,
)

__all__ = [
    # Group scoring
    "calculate_group_esg_score",
    "get_group_esg_breakdown",
    "get_top_performing_subsidiaries",
    # Trends
    "get_esg_score_trend",
    "get_pillar_trend",
    "get_year_over_year_comparison",
]
