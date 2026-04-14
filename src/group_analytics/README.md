# Group Analytics App Configuration

This is the **Layer 7: Group Consolidation & Portfolio Intelligence Engine**.

## Overview

The Group Analytics module aggregates ESG compliance intelligence and ESG scoring across subsidiaries, enabling:

- **Group ESG Dashboard**: Consolidated ESG scores across all subsidiaries
- **Subsidiary Comparison**: Side-by-side performance metrics
- **Group Compliance Intelligence**: Aggregated framework readiness, gaps, and recommendations
- **Portfolio ESG Analytics**: Investor-level reporting and portfolio summaries

## Architecture

### Selectors (Read-Only)

All aggregation logic is in selectors, following HackSoft Django Style:

- `selectors/group_readiness.py` — Framework readiness aggregation
- `selectors/group_gaps.py` — Compliance gap aggregation
- `selectors/group_recommendations.py` — Recommendation aggregation
- `selectors/group_scoring.py` — ESG score aggregation and subsidiary ranking
- `selectors/group_dashboard.py` — Unified group dashboard

### Services

Cache management and invalidation:

- `services/cache.py` — Redis caching for aggregated data

### Signals

Auto-recalculation triggers:

- `signals.py` — Invalidates caches when:
  - Framework readiness changes
  - Compliance gaps change
  - Recommendations change
  - ESG scores change
  - Organization hierarchy changes

### API Views

- `api/views.py` — 7 endpoints for group aggregation
- `api/serializers.py` — Response serialization

## API Endpoints

Base URL: `/api/v1/group/`

### Dashboards

- **GET** `/dashboard/` — Comprehensive group dashboard with all metrics
- **GET** `/portfolio-summary/` — Executive summary for investor reporting
- **GET** `/comparison/` — Side-by-side subsidiary comparison

### Aggregations

- **GET** `/esg-score/` — Aggregated ESG scores across subsidiaries
- **GET** `/framework-readiness/` — Framework readiness aggregation
- **GET** `/top-gaps/` — Top compliance gaps across group
- **GET** `/recommendations/` — Aggregated recommendations

### Rankings

- **GET** `/subsidiaries/` — Subsidiary ranking by ESG score

## Usage Examples

### Get Group Dashboard

```bash
curl -H "X-ORG-ID: {org_id}" \
  https://api.example.com/api/v1/group/dashboard/
```

Response:
```json
{
  "success": true,
  "data": {
    "esg_score": {
      "environmental": 39,
      "social": 45,
      "governance": 42,
      "overall": 42,
      "subsidiary_count": 6
    },
    "subsidiary_ranking": [ ... ],
    "framework_readiness": { ... },
    "top_gaps": [ ... ],
    "top_recommendations": [ ... ]
  }
}
```

### Get Subsidiary Ranking

```bash
curl -H "X-ORG-ID: {org_id}" \
  https://api.example.com/api/v1/group/subsidiaries/
```

Response:
```json
{
  "success": true,
  "data": [
    {
      "rank": 1,
      "org_name": "Titan Trust",
      "overall": 55,
      "environmental": 50,
      "social": 60,
      "governance": 55
    },
    ...
  ]
}
```

## Caching Strategy

Group aggregations are Redis-cached with configurable TTLs:

- Dashboard: 30 minutes
- Readiness/Scores: 1 hour
- Gaps/Recommendations: 2 hours

Cache is automatically invalidated when:
- Subsidiary data changes
- Framework assignments change
- Organization hierarchy changes

## Data Flow

```
1. Subsidiary data changes
   ↓
2. Signal triggered (post_save)
   ↓
3. Cache invalidation
   ↓
4. Next API call recalculates aggregation
   ↓
5. Result cached for TTL period
```

## Key Features

✅ **No Duplicate Models** — Reuses existing models:
- FrameworkReadiness
- ComplianceGapPriority
- ComplianceRecommendation
- ESGScore

✅ **Automatic Recalculation** — Django signals trigger cache invalidation

✅ **Performance Optimized** — Redis caching reduces database queries

✅ **Hierarchical Support** — Handles Group → Subsidiary → Facility relationships

✅ **Weighted Aggregation** — Supports simple average or weighted aggregation (by revenue, headcount, facility size)

## Models Used (Not Created)

### From compliance app
- FrameworkReadiness
- ComplianceGapPriority
- ComplianceRecommendation
- FrameworkRequirement

### From esg_scoring app
- ESGScore

### From organizations app
- Organization (parent-child relationship)
- RegulatoryFramework
- OrganizationFramework

## Configuration

No settings required. App is configured in `INSTALLED_APPS`:

```python
INSTALLED_APPS = [
    ...
    'group_analytics',
    ...
]
```

URL routing configured in main `config/urls.py`:

```python
urlpatterns = [
    ...
    path('api/v1/group/', include('group_analytics.api.urls')),
    ...
]
```

## Testing

Run selector tests:

```bash
python manage.py test group_analytics.tests.test_selectors
```

## Future Enhancements

- [ ] Weighted aggregation by revenue/headcount
- [ ] Trend analysis across multiple periods
- [ ] Anomaly detection in subsidiary performance
- [ ] Automated alerts for gaps
- [ ] Export to Excel/PDF for reports
- [ ] Custom aggregation rules per organization
