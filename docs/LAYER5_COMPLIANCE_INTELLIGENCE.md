# Layer 5 — Compliance Intelligence Engine

## Overview

The Compliance Intelligence Engine transforms raw framework mapping and coverage data into **actionable business intelligence**.

It converts:
- **Framework Mapping Data** → Framework requirements and indicator mappings
- **Coverage Metrics** → What's covered vs. uncovered
- **ESG Scores** → Performance context

Into:
- **Readiness Scores** → How ready is each organization for each framework?
- **Priority Gaps** → Which requirements need attention first?
- **Recommendations** → What specific actions solve the gaps?
- **Risk Scores** → What's the compliance risk by priority?

**This is not reporting — this is decision intelligence.**

---

## Architecture

### Three Core Components

#### 1. Framework Readiness (FrameworkReadiness Model)

Measures overall compliance preparedness for organization + framework pairs.

**Readiness Score Calculation:**
```
Readiness = (Mandatory Coverage × 0.7) + (Optional Coverage × 0.3)

Risk Levels:
- Low: Readiness ≥ 80%
- Medium: Readiness 50-79%
- High: Readiness < 50%
```

**Metrics Tracked:**
- Total requirements in framework
- Covered requirements (at least one indicator mapped)
- Coverage percentage (0-100%)
- Mandatory vs. optional coverage split
- Overall readiness score
- Risk level assessment

**Example:**
```
Organization: Total ESG Inc
Framework: GRI 2024

Total Requirements: 45
Covered: 38 (84%)
Mandatory Total: 28
Mandatory Covered: 24 (86%)

Readiness = (86% × 0.7) + (70% × 0.3) = 78%
Risk Level: MEDIUM
```

#### 2. Compliance Gap Priority (ComplianceGapPriority Model)

Ranks uncovered requirements by urgency and impact.

**Priority Scoring (0-100 points):**
```
Priority Score = 
  (Mandatory Weight: 0-40) +
  (Framework Priority: 0-30) +
  (Pillar Importance: 0-20) +
  (Coverage Impact: 0-10)

Levels:
- HIGH: Score ≥ 70
- MEDIUM: Score 40-69
- LOW: Score < 40
```

**Factors:**
- Mandatory requirement (40 points) - e.g., GRI 305-1 vs GRI 408-1
- Framework priority level (30 points) - e.g., GRI (high) vs niche framework
- Pillar importance (20 points) - ENV (15) > SOC (10) > GOV (5)
- Coverage impact (10 points) - how many indicators could satisfy this

**Example:**
```
Requirement: GRI 305-1 (Direct GHG Emissions)
Is Mandatory: Yes (40 points)
Framework Priority: 30 (GRI = 30)
Pillar: Environmental (15 points)
Potential Indicators: 5 (5 points)

Total Priority Score: 90 (HIGH)
```

#### 3. Compliance Recommendation (ComplianceRecommendation Model)

Provides specific, actionable recommendations to close gaps.

**Recommendation Types:**
- CREATE_INDICATOR - "Add Scope 1 Emissions indicator"
- ENHANCE_DATA - "Improve data collection for existing indicator"
- INTEGRATE_SYSTEM - "Connect EMS to reporting system"
- IMPLEMENT_PROCESS - "Establish governance oversight"
- TRAINING_REQUIRED - "Train board on climate risks"
- GOVERNANCE_UPDATE - "Update policy documentation"

**For each gap:**
- Generates title and description
- Provides step-by-step action plan
- Estimates effort required
- Calculates expected impact on readiness score (0-10)
- Identifies dependencies
- Links to specific resources needed

**Example:**
```
Requirement: GRI 305-1
Recommendation: "Implement Scope 1 GHG Emissions Tracking"
Type: CREATE_INDICATOR
Priority: HIGH
Impact Score: 8.5/10
Estimated Effort: 5 days

Steps:
1. Define emission source categories
2. Select data collection method (direct/activity-based)
3. Configure calculation rules
4. Set up data validation
5. Train staff
6. Enable in system
```

---

## Service Layer

### ReadinessService

```python
from compliance.services import calculate_framework_readiness

# Calculate for single framework
readiness = calculate_framework_readiness(
    organization=org,
    framework=framework,
    reporting_period=period
)

# Calculate for all frameworks
readiness_list = calculate_all_framework_readiness(
    organization=org,
    reporting_period=period
)

# Get summary by risk
summary = get_readiness_summary_by_risk(org)
# Returns: {
#   "low": {...},
#   "medium": {...},
#   "high": {...}
# }
```

### GapPriorityService

```python
from compliance.services import calculate_gap_priority, get_top_priority_gaps

# Calculate priorities for framework
gaps = calculate_gap_priority(org, framework)

# Get top gaps
top_10 = get_top_priority_gaps(org, limit=10)

# Summary by priority
summary = get_gap_summary_by_priority(org)
# Returns gaps grouped by priority level
```

### RecommendationService

```python
from compliance.services import generate_recommendations

# Generate recommendations
recs = generate_recommendations(org, framework)

# Get by priority
high_priority_recs = get_recommendations_by_priority(
    org,
    priority="high"
)

# Get summary
summary = get_recommendations_summary(org)
# Returns counts by priority and status
```

---

## API Endpoints

### Readiness Endpoints

```
GET  /api/v1/compliance/readiness/
     List all readiness scores
     
GET  /api/v1/compliance/readiness/by_risk_level/
     Group by risk level with statistics
     
POST /api/v1/compliance/readiness/recalculate/
     Trigger readiness recalculation
```

**Response Example:**
```json
{
  "id": 123,
  "organization": 1,
  "framework": "GRI",
  "readiness_score": 81.5,
  "coverage_percent": 84,
  "mandatory_coverage_percent": 78,
  "risk_level": "medium",
  "is_current": true,
  "calculated_at": "2026-04-12T10:30:00Z"
}
```

### Gap Endpoints

```
GET  /api/v1/compliance/gaps/
     List all gaps (sorted by priority)
     
GET  /api/v1/compliance/gaps/top_gaps/
     Get top 10 priority gaps
     
GET  /api/v1/compliance/gaps/by_framework/?framework_id=1
     Filter gaps by framework
     
POST /api/v1/compliance/gaps/recalculate/
     Trigger gap priority recalculation
```

**Response Example:**
```json
{
  "id": 456,
  "organization": 1,
  "framework": "GRI",
  "requirement": "GRI 305-1",
  "priority_score": 90,
  "priority_level": "high",
  "impact_category": "direct",
  "estimated_effort_days": 5,
  "is_active": true
}
```

### Recommendation Endpoints

```
GET  /api/v1/compliance/recommendations/
     List all recommendations
     
GET  /api/v1/compliance/recommendations/high_priority_pending/
     High-priority pending recommendations
     
GET  /api/v1/compliance/recommendations/summary/
     Summary counts by priority/status
     
POST /api/v1/compliance/recommendations/generate/
     Generate recommendations for framework
     
POST /api/v1/compliance/recommendations/{id}/mark_in_progress/
     Mark as in progress
     
POST /api/v1/compliance/recommendations/{id}/mark_completed/
     Mark as completed
```

### Intelligence Dashboard

```
GET /api/v1/compliance/intelligence/dashboard/
    Comprehensive compliance dashboard
```

**Response:**
```json
{
  "organization_id": 1,
  "readiness": {
    "total_frameworks": 6,
    "frameworks_on_track": 3,
    "frameworks_at_risk": 2,
    "frameworks_critical": 1,
    "avg_readiness_score": 76.5,
    "frameworks": [...]
  },
  "gaps": {
    "total": 15,
    "high_priority": 5,
    "medium_priority": 7,
    "low_priority": 3,
    "top_gaps": [...]
  },
  "recommendations": {
    "total": 15,
    "pending": 10,
    "in_progress": 3,
    "completed": 2,
    "high_priority": 8,
    "top_recommendations": [...]
  }
}
```

---

## Auto-Triggering

Recalculations are automatically triggered when:

1. **Indicator created** - New indicator added to system
2. **Framework mapping created** - New indicator-requirement mapping
3. **Indicator mapping updated** - Coverage changes
4. **Submission approved** - New data affects readiness
5. **Reporting period updated** - New period begins

**Trigger Flow:**
```
Event (Indicator Created)
  ↓
Signal Handler
  ↓
Celery Task (async)
  ↓
Calculate Readiness
  ↓
Calculate Gap Priorities
  ↓
Generate Recommendations
  ↓
Update Dashboard Cache
```

---

## Models

### FrameworkReadiness
- `organization` - FK(Organization)
- `framework` - FK(RegulatoryFramework)
- `readiness_score` - Float (0-100)
- `risk_level` - Char(low/medium/high)
- `coverage_percent` - Float (0-100)
- `mandatory_coverage_percent` - Float (0-100)
- `is_current` - Boolean

### ComplianceGapPriority
- `organization` - FK(Organization)
- `framework` - FK(RegulatoryFramework)
- `requirement` - FK(FrameworkRequirement)
- `priority_score` - Float (0-100)
- `priority_level` - Char(high/medium/low)
- `impact_category` - Char(direct/indirect/strategic)
- `estimated_effort_days` - Integer
- `is_active` - Boolean

### ComplianceRecommendation
- `organization` - FK(Organization)
- `framework` - FK(RegulatoryFramework)
- `requirement` - FK(FrameworkRequirement)
- `title` - CharField
- `description` - TextField
- `recommendation_type` - Char (create_indicator/enhance_data/etc)
- `priority` - Char(high/medium/low)
- `impact_score` - Float (0-10)
- `estimated_effort_days` - Integer
- `status` - Char(pending/in_progress/completed/deferred)
- `actionable_steps` - JSONField

---

## Example Workflow

### Step 1: Organization Views Dashboard
```
GET /api/v1/compliance/intelligence/dashboard/

Response: Organization has 6 frameworks
- 3 on track (green)
- 2 at risk (yellow)
- 1 critical (red)
Average readiness: 76.5%
```

### Step 2: Check Critical Framework
```
GET /api/v1/compliance/readiness/?framework_id=1&risk_level=high

Response: TCFD Framework
- Readiness: 42%
- Coverage: 45% (6/13 requirements)
- Risk: HIGH
```

### Step 3: Identify Gaps
```
GET /api/v1/compliance/gaps/by_framework/?framework_id=1

Response: Top 5 gaps
1. TCFD Governance (Priority: 95, Mandatory)
2. TCFD Scenario Analysis (Priority: 88, Mandatory)
3. TCFD Transition Plan (Priority: 82, Mandatory)
4. TCFD Strategy (Priority: 75, Optional)
5. TCFD Targets (Priority: 68, Optional)
```

### Step 4: Get Recommendations
```
GET /api/v1/compliance/recommendations/high_priority_pending/

Response: 8 high-priority recommendations
1. "Establish Board Governance for Climate Risk" (10 days)
2. "Implement Climate Scenario Analysis" (15 days)
3. "Define Transition Strategy" (12 days)
...
```

### Step 5: Start Implementation
```
POST /api/v1/compliance/recommendations/123/mark_in_progress/

Response: Recommendation status → IN_PROGRESS
```

### Step 6: Track Progress
```
GET /api/v1/compliance/recommendations/summary/

Response:
{
  "total": 15,
  "pending": 7,
  "in_progress": 5,
  "completed": 3,
  "high_priority": 8
}
```

### Step 7: Verify Progress
```
GET /api/v1/compliance/readiness/?framework_id=1

Response: TCFD Framework (updated)
- Readiness: 58% (↑16%)
- Coverage: 62% (8/13 requirements)
- Risk: MEDIUM (↑ from HIGH)
```

---

## Admin Panels

### Framework Readiness Admin
- View all readiness scores
- Filter by risk level, framework, organization
- Color-coded readiness badges:
  - 🟢 Green: 80%+
  - 🟡 Yellow: 50-79%
  - 🔴 Red: <50%

### Compliance Gap Priority Admin
- View prioritized gaps
- Filter by priority level, impact category
- Sort by priority score
- Edit gap descriptions and effort estimates

### Compliance Recommendation Admin
- View all recommendations
- Filter by status, priority, type
- Bulk actions: Mark In Progress, Mark Completed
- Track completion timeline

---

## Performance Considerations

### Caching
- Readiness scores cached for 1 hour
- Gaps refreshed when requirements change
- Dashboard computed nightly

### Database Queries
- Optimized with select_related/prefetch_related
- Indexes on (organization, framework, status)
- Aggregation queries use database-level COUNT/AVG

### Async Processing
- All calculations run via Celery
- Non-blocking UI interactions
- Batch recalculation overnight

---

## Future Enhancements

1. **ML-Powered Recommendations** - Use historical data to predict effort/impact
2. **Compliance Roadmap** - Create multi-year compliance execution plans
3. **Peer Benchmarking** - Compare readiness vs. peer organizations
4. **Automated Actions** - Auto-create indicators based on recommendation templates
5. **Real-time Alerts** - Notify on critical compliance risks
6. **Integration with BI Tools** - Connect to Tableau, Power BI for deeper analysis

---

## Tech Stack

- **Models**: Django ORM with PostgreSQL
- **Services**: HackSoft service layer pattern
- **API**: Django REST Framework with drf-spectacular
- **Async**: Celery with Redis
- **Authentication**: Token + X-ORG-ID multi-tenant
- **Admin**: Django admin with custom panels

---

## Testing

Run comprehensive test suite for Layer 5:
```bash
python manage.py test compliance --verbosity=2
```

Tests cover:
- Readiness calculation accuracy
- Gap priority scoring
- Recommendation generation
- API endpoints
- Signal triggering
- Celery task execution
