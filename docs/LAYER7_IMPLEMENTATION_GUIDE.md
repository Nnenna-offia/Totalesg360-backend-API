# Layer 7: Group Consolidation & Portfolio Intelligence Engine — Implementation Guide

**Completed:** Layer 7 Group Analytics module has been fully implemented.

## Implementation Summary

### ✅ What Was Built

#### 1. **Folder Structure**
```
src/group_analytics/
├── migrations/
├── selectors/
│   ├── __init__.py
│   ├── group_readiness.py
│   ├── group_gaps.py
│   ├── group_recommendations.py
│   ├── group_scoring.py
│   └── group_dashboard.py
├── services/
│   ├── __init__.py
│   └── cache.py
├── api/
│   ├── __init__.py
│   ├── views.py
│   ├── serializers.py
│   └── urls.py
├── tests/
│   ├── __init__.py
│   └── test_selectors.py
├── __init__.py
├── app.py
├── admin.py
├── signals.py
└── README.md
```

#### 2. **Selector Functions** (aggregation-only)

All selectors query existing models without creating new ones:

**group_readiness.py:**
- `get_group_framework_readiness()` — Framework readiness across subsidiaries
- `get_group_readiness_summary()` — Simple readiness summary

**group_gaps.py:**
- `get_group_top_gaps()` — Top compliance gaps by affected subsidiaries
- `get_group_gap_summary()` — Gap statistics summary

**group_recommendations.py:**
- `get_group_recommendations()` — Aggregated recommendations
- `get_group_recommendations_summary()` — Recommendation statistics

**group_scoring.py:**
- `calculate_group_esg_score()` — Aggregated ESG scores (simple or weighted average)
- `get_subsidiary_ranking()` — Subsidiaries ranked by ESG score
- `get_group_esg_trend()` — ESG score trends over periods
- `_calculate_subsidiary_weight()` — Future enhancement for weighted aggregation

**group_dashboard.py:**
- `get_group_dashboard()` — Comprehensive group dashboard combining all metrics
- `get_subsidiary_comparison()` — Side-by-side subsidiary comparison
- `get_group_portfolio_summary()` — Executive summary for investor reporting

#### 3. **API Endpoints** (7 endpoints)

Base URL: `/api/v1/group/`

**Dashboards:**
- `GET /dashboard/` — Comprehensive group dashboard
- `GET /portfolio-summary/` — Executive investor summary
- `GET /comparison/` — Subsidiary comparison

**Aggregations:**
- `GET /esg-score/` — Group ESG score
- `GET /framework-readiness/` — Framework readiness aggregation
- `GET /top-gaps/` — Top compliance gaps
- `GET /recommendations/` — Aggregated recommendations

**Rankings:**
- `GET /subsidiaries/` — Subsidiary ranking

#### 4. **Caching Strategy**

File: `services/cache.py`

- **Cache TTLs:**
  - Dashboard: 30 minutes (frequently accessed)
  - Readiness/Scores: 1 hour
  - Gaps/Recommendations: 2 hours

- **Cache Keys:**
  - Per organization
  - Per reporting period
  - Automatic invalidation on data changes

- **Cache Functions:**
  - `invalidate_group_cache()` — Clear all caches for group
  - `invalidate_parent_cache()` — Clear parent caches when subsidiary changes
  - Set/get cache for each aggregation type

#### 5. **Auto-Recalculation Signals**

File: `signals.py`

Django signals automatically invalidate caches when:
- ✅ `FrameworkReadiness` changes
- ✅ `ComplianceGapPriority` changes
- ✅ `ComplianceRecommendation` changes
- ✅ `ESGScore` changes
- ✅ `Organization` hierarchy changes

Flow:
```
1. Subsidiary data changes (e.g., readiness updated)
   ↓
2. Signal triggered (post_save)
   ↓
3. Cache invalidated for parent organization
   ↓
4. Next API call recalculates aggregation
   ↓
5. Result cached for TTL period
```

#### 6. **Data Reuse** (No Duplicate Models)

Models used (NOT created):
- ✅ `FrameworkReadiness` — from compliance app
- ✅ `ComplianceGapPriority` — from compliance app
- ✅ `ComplianceRecommendation` — from compliance app
- ✅ `ESGScore` — from esg_scoring app
- ✅ `Organization` (parent-child relationship) — already exists
- ✅ `RegulatoryFramework` — from organizations app

#### 7. **Project Configuration**

**Updated `config/settings/base.py`:**
```python
INSTALLED_APPS = [
    ...
    'group_analytics',  # Added
]
```

**Updated `config/urls.py`:**
```python
urlpatterns = [
    ...
    path('api/v1/group/', include('group_analytics.api.urls')),  # Added
]
```

### 📊 Sample Response Data

#### Get Group Dashboard

```json
{
  "success": true,
  "data": {
    "organization": {
      "id": "org-123",
      "name": "TGI Group",
      "type": "group"
    },
    "esg_score": {
      "environmental": 39,
      "social": 45,
      "governance": 42,
      "overall": 42,
      "subsidiary_count": 6,
      "calculation_method": "simple_average",
      "subsidiaries": [
        {
          "org_id": "org-1",
          "org_name": "WACOT Rice",
          "environmental": 40,
          "social": 50,
          "governance": 40,
          "overall": 43,
          "weight": null
        },
        ...
      ]
    },
    "subsidiary_ranking": [
      {
        "rank": 1,
        "org_id": "org-1",
        "org_name": "Titan Trust",
        "environmental": 50,
        "social": 60,
        "governance": 55,
        "overall": 55,
        "organization_type": "subsidiary",
        "change": null
      },
      ...
    ],
    "framework_readiness": {
      "frameworks": [
        {
          "code": "GRI",
          "name": "Global Reporting Initiative",
          "avg_readiness": 62,
          "risk_level": "medium",
          "subsidiary_count": 6,
          "low_risk_count": 1,
          "medium_risk_count": 3,
          "high_risk_count": 2,
          "subsidiaries": [...]
        }
      ],
      "parent_readiness": {...},
      "total_subsidiaries": 6
    },
    "top_gaps": [
      {
        "requirement_id": "req-123",
        "requirement_code": "305-1",
        "requirement_name": "Scope 1 Emissions",
        "framework_code": "GRI",
        "affected_subsidiaries": 3,
        "priority": "high",
        "high_priority_count": 3,
        "medium_priority_count": 0,
        "low_priority_count": 0,
        "organizations": [
          {
            "org_id": "org-1",
            "org_name": "Subsidiary A",
            "gap_priority": "high",
            "priority_score": 85.0
          }
        ]
      }
    ],
    "top_recommendations": [
      {
        "recommendation_id": "rec-123",
        "title": "Implement Scope 1 emissions tracking",
        "recommendation_type": "create_indicator",
        "affected_subsidiaries": 3,
        "priority": "high",
        "organizations": [...]
      }
    ]
  }
}
```

#### Get Subsidiary Ranking

```json
{
  "success": true,
  "data": [
    {
      "rank": 1,
      "org_id": "org-1",
      "org_name": "Titan Trust",
      "environmental": 50,
      "social": 60,
      "governance": 55,
      "overall": 55,
      "organization_type": "subsidiary"
    },
    {
      "rank": 2,
      "org_id": "org-2",
      "org_name": "WACOT Rice",
      "environmental": 40,
      "social": 50,
      "governance": 40,
      "overall": 43,
      "organization_type": "subsidiary"
    }
  ]
}
```

### 🔌 Integration Points

#### 1. **Organization Hierarchy Support**

Already supported by Organization model:
```python
parent = models.ForeignKey(
    "self",
    null=True,
    blank=True,
    related_name="subsidiaries",
    on_delete=models.CASCADE
)
```

Usage in selectors:
```python
subsidiaries = Organization.objects.filter(parent=parent_organization)
```

#### 2. **Signal Integration**

Signals automatically connect to compliance & ESG scoring:
- Defined in `signals.py`
- Auto-imported in `app.py` ready() method
- Monitor: FrameworkReadiness, ComplianceGapPriority, ComplianceRecommendation, ESGScore

#### 3. **Cache Integration**

Uses Django's cache framework (configured in settings):
```python
from django.core.cache import cache
cache.set(key, value, timeout)
cache.get(key)
cache.delete(key)
```

#### 4. **API Permission System**

Uses existing permissions:
```python
permission_classes = [IsAuthenticated, IsOrgMember]
```

### 🧪 Testing

Basic test suite provided: `tests/test_selectors.py`

Run tests:
```bash
python manage.py test group_analytics.tests.test_selectors
```

Tests cover:
- Group readiness aggregation
- Group ESG score calculation
- Dashboard generation

### 📈 Response Aggregation Examples

#### Framework Readiness Aggregation

Input: 3 subsidiaries with different readiness levels

```
Subsidiary 1: 70% (MEDIUM)
Subsidiary 2: 80% (LOW)
Subsidiary 3: 60% (HIGH)
```

Output:
```json
{
  "code": "GRI",
  "avg_readiness": 70,
  "risk_level": "medium",
  "subsidiary_count": 3,
  "low_risk_count": 1,
  "medium_risk_count": 1,
  "high_risk_count": 1
}
```

#### ESG Score Aggregation

Input: 2 subsidiaries with E/S/G scores

```
Sub 1: E=40, S=45, G=38 → Overall=41
Sub 2: E=50, S=55, G=52 → Overall=52
```

Output:
```json
{
  "environmental": 45,   // (40+50)/2
  "social": 50,          // (45+55)/2
  "governance": 45,      // (38+52)/2
  "overall": 46.5        // (41+52)/2
}
```

### 🚀 Deployment Checklist

- [x] Add `group_analytics` to INSTALLED_APPS
- [x] Add group analytics URLs to config/urls.py
- [x] Run migrations (no new DB models needed)
- [x] Test selectors with existing data
- [x] Verify cache framework is configured in settings
- [x] Test API endpoints with proper X-ORG-ID header
- [x] Verify signals are connected

### 🔄 Future Enhancements

1. **Weighted Aggregation**
   - By revenue
   - By employee count
   - By facility size
   - Custom weights per organization

2. **Trend Analysis**
   - Score changes over periods
   - Gap progression
   - Recommendation completion rates

3. **Anomaly Detection**
   - Alert on score drops
   - Identify underperforming subsidiaries
   - Flag unusual gap patterns

4. **Advanced Reporting**
   - Export to Excel/PDF
   - Custom aggregation rules
   - Scheduled reports
   - Investor-facing dashboards

5. **Real-Time Updates**
   - WebSocket integration for live dashboards
   - Push notifications for significant changes
   - Streaming score updates

### 📚 Documentation Structure

1. **README.md** — Quick start and feature overview
2. **This file** — Complete implementation guide
3. **API Docstrings** — Inline view/selector documentation
4. **Test Suite** — Usage examples

### 🎯 Success Criteria Met

✅ Layer 7 Group Consolidation Engine implemented
✅ No duplicate models (reuses existing models)
✅ Aggregation-only (no new data storage)
✅ 7 API endpoints for group intelligence
✅ Auto-recalculation via signals
✅ Redis caching for performance
✅ Parent-child organization hierarchy support
✅ Subsidiary comparison and ranking
✅ Group ESG dashboard
✅ Portfolio intelligence for investors
✅ Framework readiness aggregation
✅ Compliance gap aggregation
✅ Recommendation aggregation
✅ ESG score aggregation

---

**Implementation completed on:** 2026-04-13

**Architecture follows:** HackSoft Django Style Guide
- Selectors for read-only queries
- Services for business logic
- Signals for auto-recalculation
- No duplicate models
- Atomic operations
- Structured logging

**Ready for:** Production deployment
