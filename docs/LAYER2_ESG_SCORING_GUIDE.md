# Layer 2: ESG Scoring Engine - Implementation Guide

## Overview

Totalesg360 Layer 2 implements an enterprise-grade ESG scoring system that calculates Environmental, Social, and Governance scores for organizations based on indicator submissions and target goals.

### Architecture Pattern: HackSoft Service-Oriented

Layer 2 follows the same HackSoft architecture as Layer 1:
- **Models**: Domain objects storing calculated scores
- **Services**: Business logic for score calculations
- **Selectors**: Read-only queries and analysis
- **API Views**: REST endpoints with permission checks
- **Serializers**: Input validation and response formatting

## Core Components

### 1. Domain Models

#### IndicatorScore
Stores calculated scores for individual indicators per organization per reporting period.

```
Organization + Indicator + ReportingPeriod → IndicatorScore
```

**Fields:**
- `organization` (FK): Organization being scored
- `indicator` (FK): Indicator being scored  
- `reporting_period` (FK): Reporting period
- `score` (0-100): Calculated score
- `value`: Actual aggregated value from submissions
- `target`: Target goal value
- `baseline`: Baseline value for comparison
- `progress` (0-100): Progress percentage toward target
- `status`: POOR | AT_RISK | ON_TRACK | ACHIEVED
- `calculation_method`: E.g., "linear_progress"
- `is_manual`: True if manually entered
- `note`: Optional explanatory text

**Unique Constraint:** (organization, indicator, reporting_period)

**Methods:**
- `is_on_track()`: Check if status is ON_TRACK or ACHIEVED
- `is_at_risk()`: Check if status is AT_RISK or POOR

#### PillarScore
Stores aggregated scores for E/S/G pillars.

```
IndicatorScores (for a pillar) → PillarScore (average)
```

**Fields:**
- `organization` (FK): Organization
- `reporting_period` (FK): Reporting period
- `pillar`: ENVIRONMENTAL | SOCIAL | GOVERNANCE
- `score` (0-100): Average of all indicator scores under this pillar
- `indicator_count`: Number of indicators aggregated
- `on_track_count`: Indicators with ON_TRACK or ACHIEVED status
- `at_risk_count`: Indicators with AT_RISK or POOR status
- `is_dirty`: Cache invalidation flag

**Unique Constraint:** (organization, pillar, reporting_period)

**Methods:**
- `get_health_status()`: Returns "Excellent" (≥76), "Good" (51-75), "Fair" (26-50), "Poor" (<26)
- `get_risk_percentage()`: Percentage of at-risk indicators

#### ESGScore
Stores overall ESG scores combining all pillars.

```
PillarScores (E, S, G) → ESGScore (weighted average)
```

**Fields:**
- `organization` (FK): Organization
- `reporting_period` (FK): Reporting period
- `environmental_score` (0-100): E pillar
- `social_score` (0-100): S pillar
- `governance_score` (0-100): G pillar
- `overall_score` (0-100): Weighted average
- `environmental_weight` (default 0.4): Configurable
- `social_weight` (default 0.3): Configurable
- `governance_weight` (default 0.3): Configurable
- `is_consolidated`: True for group scores, False for org scores
- `is_dirty`: Cache invalidation flag

**Unique Constraint:** (organization, reporting_period)

**Methods:**
- `get_score_distribution()`: Returns dict of all scores
- `get_pillar_ranking()`: Ranked list [best → worst]
- `get_strengths()`: Pillars with score ≥ 70
- `get_weaknesses()`: Pillars with score < 50

### 2. Service Layer

#### indicator_scoring.py
Calculates foundation-level indicator scores.

**Main Functions:**

1. `calculate_indicator_score(organization, indicator, period)`
   - Aggregates submission values for indicator
   - Compares against target goal
   - Calculates progress: `(baseline - current) / (baseline - target) * 100`
   - Supports direction-aware calculation (↑ increase vs ↓ decrease indicators)
   - Assigns status based on progress bands
   - Returns IndicatorScore

2. `calculate_all_indicator_scores(organization, period)`
   - Calculates all indicators for organization

3. `batch_calculate_indicator_scores(organizations, period)`
   - Calculates for multiple organizations

#### pillar_scoring.py
Aggregates indicator scores into pillar scores.

**Main Functions:**

1. `calculate_pillar_score(organization, pillar, period)`
   - Gets all indicators under pillar
   - Retrieves their indicator scores
   - Averages them: `pillar_score = avg(indicator_scores)`
   - Counts on_track vs at_risk distribution
   - Returns PillarScore

2. `calculate_all_pillar_scores(organization, period)`
   - Calculates all 3 pillars (E, S, G)

3. `get_pillar_scores_dict(organization, period)`
   - Returns simple dict: `{'environmental': 42.5, 'social': 38.2, 'governance': 51.0}`

#### esg_scoring.py
Top-level ESG score calculation with weighted aggregation.

**Main Functions:**

1. `calculate_esg_score(organization, period, weights, is_consolidated)`
   - Ensures all 3 pillar scores exist
   - Retrieves pillar scores
   - Applies weighted calculation:
     ```
     overall = (environmental * 0.4) + 
               (social * 0.3) + 
               (governance * 0.3)
     ```
   - Normalizes weights if needed
   - Returns ESGScore with is_consolidated flag

2. `calculate_esg_scores_for_all_organizations(period, org_ids, weights)`
   - Batch scoring for multiple organizations

3. `get_esg_score_summary(organization, period)`
   - Frontend-friendly dict with:
     - `overall`, `environmental`, `social`, `governance` scores
     - `strengths` (≥70), `weaknesses` (<50)
     - `ranking` (sorted pillars)
     - `calculated_at` timestamp

### 3. Selector Layer

#### group_scoring.py
Group consolidation queries.

**Main Functions:**

1. `calculate_group_esg_score(parent_org, period, weights, include_parent)`
   - Gets all subsidiaries
   - Aggregates their scores
   - Creates consolidated group score

2. `get_group_esg_breakdown(parent_org, period)`
   - Returns group score + subsidiary breakdown

3. `get_top_performing_subsidiaries(parent_org, period, limit)`
   - Returns top N subsidiaries by score

#### trends.py
Historical analysis queries.

**Main Functions:**

1. `get_esg_score_trend(organization, periods)`
   - Returns trend data over N periods
   - Includes statistics (latest, average, high, low)

2. `get_pillar_trend(organization, pillar, periods)`
   - Pillar-specific trend

3. `get_year_over_year_comparison(organization, periods)`
   - YoY comparison with change percentage

4. `get_indicator_trend(organization, indicator_id, periods)`
   - Indicator-specific trend

### 4. API Layer

#### Endpoints

All endpoints require `X-ORG-ID` header for multi-tenant context.

**ViewSet: ESGScoreViewSet**

- `GET /api/v1/esg/scores/` - List organization's ESG scores
- `GET /api/v1/esg/scores/{id}/` - Retrieve specific score
- `GET /api/v1/esg/scores/current/` - Get latest score
- `POST /api/v1/esg/scores/calculate/` - Trigger recalculation
- `GET /api/v1/esg/scores/summary/` - Summary for frontend
- `GET /api/v1/esg/scores/trend/` - Trend analysis
- `GET /api/v1/esg/scores/group-breakdown/` - Group consolidation
- `GET /api/v1/esg/scores/top-performers/` - Top subsidiaries

**ViewSet: IndicatorScoreViewSet** (Read-only)

- `GET /api/v1/esg/indicators/` - List indicator scores

**ViewSet: PillarScoreViewSet** (Read-only)

- `GET /api/v1/esg/pillars/` - List pillar scores

#### Serializers

- `IndicatorScoreSerializer`: Input validation + response
- `IndicatorScoreDetailSerializer`: Detailed with relationships
- `PillarScoreSerializer`: Pillar score response
- `ESGScoreSerializer`: ESG score response with strengths/weaknesses
- `ScoreSummarySerializer`: Frontend summary format
- `CalculateScoreSerializer`: Trigger calculation request
- `ScoreTrendDataSerializer`: Trend analysis response
- `GroupScoreSummarySerializer`: Group breakdown response

## Scoring Logic

### Score Status Bands

```
ACHIEVED (On Target):  76-100  ✓ Excellent performance
ON_TRACK (Good):       51-75   → Good progress  
AT_RISK (Caution):     26-50   ⚠ Needs improvement
POOR (Critical):       0-25    ✗ Critical issues
```

### Progress Calculation

For **INCREASE indicators** (e.g., compliance ↑):
```
progress = (current - baseline) / (target - baseline) * 100
```
Example: baseline=40%, current=70%, target=90%
→ progress = (70-40)/(90-40) = 60%

For **DECREASE indicators** (e.g., emissions ↓):
```
progress = (baseline - current) / (baseline - target) * 100
```
Example: baseline=100 tons, current=60 tons, target=20 tons
→ progress = (100-60)/(100-20) = 50%

### Weight Configuration

Default weights (configurable per organization/period):
- Environmental: 40%
- Social: 30%
- Governance: 30%

Overall ESG Score:
```
overall = (E_score × 0.4) + (S_score × 0.3) + (G_score × 0.3)
```

## Installation & Setup

### 1. Add to INSTALLED_APPS

Edit `config/settings/base.py`:
```python
INSTALLED_APPS = [
    ...
    'esg_scoring.apps.EsgScoringConfig',
]
```

### 2. Run Migrations

```bash
python manage.py makemigrations esg_scoring
python manage.py migrate esg_scoring
```

### 3. Verify Installation

```bash
python manage.py check
```

## Usage Examples

### Calculate Scores

```python
from esg_scoring.services import (
    calculate_indicator_score,
    calculate_all_pillar_scores,
    calculate_esg_score,
)
from organizations.models import Organization
from submissions.models import ReportingPeriod

org = Organization.objects.get(name="Acme Corp")
period = ReportingPeriod.objects.get(name="Q1 2024")

# Calculate indicator scores
calculate_all_indicator_scores(org, period)

# Calculate pillar scores
calculate_all_pillar_scores(org, period)

# Calculate overall ESG score
esg_score = calculate_esg_score(org, period)
print(f"ESG Score: {esg_score.overall_score}")
```

### Retrieve Scores

```python
from esg_scoring.models import ESGScore
from esg_scoring.services import get_esg_score_summary

score = ESGScore.objects.get(organization=org, reporting_period=period)

# Get summary for frontend
summary = get_esg_score_summary(org, period)
# Returns: {
#   'overall': 43.0,
#   'environmental': 42.0,
#   'social': 38.0,
#   'governance': 51.0,
#   'strengths': [('Governance', 51.0)],
#   'weaknesses': [('Social', 38.0), ('Environmental', 42.0)],
#   'ranking': ['Governance', 'Environmental', 'Social'],
#   'calculated_at': '2024-01-15T10:30:00'
# }
```

### Analyze Trends

```python
from esg_scoring.selectors.trends import get_esg_score_trend

trend = get_esg_score_trend(org, periods=12)
# Returns historical trend with statistics

print(f"Latest: {trend['statistics']['latest_score']}")
print(f"Average: {trend['statistics']['average_score']}")
```

### Group Consolidation

```python
from esg_scoring.selectors.group_scoring import (
    calculate_group_esg_score,
    get_top_performing_subsidiaries,
)

parent_org = Organization.objects.get(name="Global Corp")

# Calculate group score
group_score = calculate_group_esg_score(parent_org, period)

# Get top performers
top = get_top_performing_subsidiaries(parent_org, period, limit=5)
```

## Management Commands

### Calculate ESG Scores

```bash
# Calculate for all active organizations
python manage.py calculate_esg_scores --all

# Calculate for specific organization
python manage.py calculate_esg_scores --org-id <org-uuid>

# Calculate for specific period
python manage.py calculate_esg_scores --period-id <period-uuid>
```

## Celery Tasks (Phase 2)

Async scoring tasks for bulk processing:
- `calculate_org_indicator_scores.delay(org_id, period_id)`
- `calculate_org_pillar_scores.delay(org_id, period_id)`
- `calculate_org_esg_score.delay(org_id, period_id)`
- `batch_calculate_all_scores.delay(period_id)`
- `calculate_group_consolidation.delay(group_id, period_id)`

## Signal Handlers (Phase 2)

Auto-trigger calculations on:
- Post-save submission → trigger indicator recalculation
- Post-save activity → trigger pillar recalculation
- Post-save target → recalculate all scores
- Reporting period close → group consolidation

## Caching (Phase 2)

- Cache ESG scores with configurable TTL
- Invalidate on signal using `is_dirty` flags
- Use `is_consolidated` to distinguish group vs org scores

## Security & Permissions

All API endpoints require:
- **Authentication**: JWT in HttpOnly cookies
- **Authorization**: `IsAuthenticated` + `IsOrgMember` permissions
- **Multi-tenancy**: `X-ORG-ID` header context

## Testing

Comprehensive test suite (Phase 2 implementation):
- Model tests: constraints, methods, validations
- Service tests: calculation scenarios, edge cases
- API tests: endpoints, permissions, response formats
- Integration tests: full scoring pipeline

## Database Schema

### Tables
- `esg_scoring_indicator_score` - Individual indicator scores
- `esg_scoring_pillar_score` - Aggregated pillar scores
- `esg_scoring_esg_score` - Overall ESG scores

### Indexes
- `(organization, reporting_period)` - Fast org/period lookups
- `(pillar, reporting_period)` - Fast pillar lookups
- `(status, reporting_period)` - Status filtering
- `(is_consolidated, reporting_period)` - Group score filtering

## Next Steps

**Phase 2 Implementation:**
1. ✓ Models (completed)
2. ✓ Services (completed)
3. ✓ Selectors (completed)
4. ✓ API Views & Serializers (completed)
5. Signal handlers for auto-triggering
6. Celery tasks for async processing
7. Caching layer with invalidation
8. Comprehensive test suite (50+ tests)
9. Complete documentation

**Roadmap:**
- Dashboard visualizations (Layer 3)
- Compliance tracking (Layer 4)
- Regulatory reporting templates (Layer 5)
