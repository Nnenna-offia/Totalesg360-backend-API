# TargetGoal Refactoring: Reporting Frequency Architecture

## Overview

This refactoring enables **multi-year targets** with **flexible reporting frequencies**. Instead of fixing targets to a single ReportingPeriod, targets now reference a ReportingFrequency, and the system dynamically resolves all matching periods across the target's year range.

**Key Principle**: Targets span **multiple reporting periods across multiple years**, and ReportingPeriods are **auto-generated per year**.

---

## 1. Model Changes

### TargetGoal Model

Added `ReportingFrequency` enum and `reporting_frequency` field:

```python
class TargetGoal(BaseModel):
    class ReportingFrequency(models.TextChoices):
        DAILY = "DAILY", "Daily"
        WEEKLY = "WEEKLY", "Weekly"
        BI_WEEKLY = "BI_WEEKLY", "Bi-Weekly"
        MONTHLY = "MONTHLY", "Monthly"
        QUARTERLY = "QUARTERLY", "Quarterly"
        SEMI_ANNUAL = "SEMI_ANNUAL", "Semi-Annual"
        ANNUAL = "ANNUAL", "Annual"

    reporting_frequency = models.CharField(
        max_length=20,
        choices=ReportingFrequency.choices,
        default=ReportingFrequency.ANNUAL,
        db_index=True,
        help_text="Reporting frequency for this target"
    )
```

**Fields**:
- `organization` - Organization owning the target
- `indicator` - The KPI being tracked
- `department` - Department responsible (optional)
- `facility` - Facility scope (optional)
- `reporting_frequency` - How often this target reports (DAILY, WEEKLY, ..., ANNUAL)
- `baseline_year` - Starting year
- `baseline_value` - Baseline value
- `target_year` - Target completion year
- `target_value` - Target value to achieve
- `direction` - INCREASE or DECREASE
- `status` - ACTIVE, COMPLETED, ARCHIVED

**Removed**:
- ~~`reporting_period_id`~~ - No longer stores a single period FK

---

## 2. Serializers

### TargetGoalCreateSerializer

Frontend now sends `reporting_frequency` instead of `reporting_period_id`:

```json
{
  "indicator_id": "uuid",
  "reporting_frequency": "QUARTERLY",
  "baseline_year": 2025,
  "baseline_value": 100,
  "target_year": 2028,
  "target_value": 75,
  "direction": "decrease"
}
```

**Fields**:
- `indicator_id` (required)
- `facility_id` (optional)
- `department_id` (optional)
- `name` (required)
- `description` (optional)
- `reporting_frequency` (required) - One of 7 frequencies
- `baseline_year` (required)
- `baseline_value` (required)
- `target_year` (required)
- `target_value` (required)
- `direction` (default: decrease)

### TargetGoalPatchSerializer

Allows updating `reporting_frequency` and all other fields except `organization`:

```python
{
  "reporting_frequency": "SEMI_ANNUAL",
  "target_year": 2029,
  "target_value": 60
}
```

---

## 3. Dynamic Period Resolution Selector

### File: `src/targets/selectors/reporting_periods.py`

```python
def get_target_reporting_periods(goal: TargetGoal) -> List[ReportingPeriod]:
    """
    Dynamically fetch ReportingPeriods matching a target goal's frequency and year range.
    
    Automatically ensures periods exist for the target's year range.
    
    Example:
        Target: Quarterly 2025 → 2028
        Returns: 16 quarters (Q1-Q4 for 2025, 2026, 2027, 2028)
    """
```

**Behavior**:
1. Calls `ensure_reporting_periods_exist()` to auto-generate missing periods
2. Queries ReportingPeriods matching:
   - `organization` = target's org
   - `period_type` = target's reporting_frequency
   - `start_date__year` >= baseline_year
   - `end_date__year` <= target_year
   - `is_active` = True
3. Returns ordered by `start_date`

---

## 4. Auto-Generation Service

### File: `src/targets/services/reporting_period_service.py`

```python
def ensure_reporting_periods_exist(
    organization,
    start_year: int,
    end_year: int,
    frequency: str
) -> int:
    """
    Ensure ReportingPeriods exist for all years in a target's range.
    
    If periods are missing for a given year, auto-generates them.
    """
```

**Behavior**:
1. Queries existing years for `org + frequency`
2. For each missing year, calls `generate_reporting_periods()`
3. Returns count of newly generated periods
4. Gracefully handles generation failures (logs warning, continues)

**Example**:
```python
ensure_reporting_periods_exist(
    organization=my_org,
    start_year=2025,
    end_year=2028,
    frequency="QUARTERLY"
)
# Result: If Q1-Q4 don't exist for 2025, 2026, 2027, 2028, they are created
```

---

## 5. Progress Computation Flow

### Flow Diagram

```
TargetGoal (reporting_frequency=QUARTERLY, 2025→2028)
    ↓
get_target_reporting_periods(goal)
    ↓
[Ensure periods exist for 2025-2028]
    ↓
Fetch 16 quarterly periods (Q1-Q4 × 4 years)
    ↓
DataSubmission.objects.filter(
    indicator=goal.indicator,
    reporting_period__in=periods
)
    ↓
calculate_target_progress(goal)
    ↓
{
    progress_percent: 0-100,
    status: 'pending|at_risk|on_track|achieved',
    current_value: float
}
```

---

## 6. API Changes

### Create Target

**Request**:
```http
POST /api/v1/targets/goals/
X-ORG-ID: org-uuid

{
  "indicator_id": "ind-uuid",
  "reporting_frequency": "QUARTERLY",
  "baseline_year": 2025,
  "baseline_value": 100,
  "target_year": 2028,
  "target_value": 50,
  "direction": "decrease",
  "name": "Reduce Waste",
  "description": "Reduce waste by 50% by 2028"
}
```

**Response**:
```json
{
  "success": true,
  "data": {
    "goal_id": "goal-uuid"
  }
}
```

### Update Target

**Request**:
```http
PATCH /api/v1/targets/goals/{goal_id}/
X-ORG-ID: org-uuid

{
  "reporting_frequency": "SEMI_ANNUAL",
  "target_year": 2029
}
```

**Response**:
```json
{
  "success": true,
  "data": {
    "goal_id": "goal-uuid"
  }
}
```

### Get Target Progress

**Request**:
```http
GET /api/v1/targets/goals/{goal_id}/progress/
X-ORG-ID: org-uuid
```

**Response** (using new selector):
```json
{
  "success": true,
  "data": {
    "progress": {
      "progress_percent": 45,
      "status": "on_track",
      "current_value": 55
    }
  }
}
```

---

## 7. Example Workflow

### Scenario: Create Quarterly Target

**User Request**:
- Reduce emissions quarterly from 2025-2028
- Baseline: 100 tonnes (Q1 2025)
- Target: 50 tonnes (Q4 2028)

**Frontend Sends**:
```json
{
  "indicator_id": "emissions-uuid",
  "reporting_frequency": "QUARTERLY",
  "baseline_year": 2025,
  "baseline_value": 100,
  "target_year": 2028,
  "target_value": 50,
  "direction": "decrease"
}
```

**Backend Process**:
1. Create TargetGoal with `reporting_frequency="QUARTERLY"`
2. When calculating progress:
   - Call `get_target_reporting_periods(goal)`
   - Auto-generate Q1-Q4 2025, 2026, 2027, 2028 if missing
   - Fetch 16 quarterly periods
   - Query DataSubmission for emissions across all 16 periods
   - Compute progress: (baseline - current) / (baseline - target)

**Example Result**:
- Current value: 55 tonnes
- Progress: (100 - 55) / (100 - 50) = 45 / 50 = 90%
- Status: "on_track" (>70%)

---

## 8. Integration Points

### Services Used

- **`submissions.services.period_generation.generate_reporting_periods()`**
  - Generates periods for missing years
  - Used by `ensure_reporting_periods_exist()`

- **`targets.services.target_progress_service.calculate_target_progress()`**
  - Computes progress using DataSubmissions
  - Called after periods are resolved

### Selectors Used

- **`targets.selectors.reporting_periods.get_target_reporting_periods()`**
  - Resolves periods for a target
  - Auto-ensures periods exist

- **`targets.selectors.target_selectors.get_indicator_current_value()`**
  - Fetches latest value from DataSubmission
  - Scoped to resolved periods

---

## 9. Database Schema

### TargetGoal Table

```sql
-- New field added in migration 0003_add_reporting_frequency
ALTER TABLE targets_targetgoal 
ADD COLUMN reporting_frequency VARCHAR(20) 
NOT NULL DEFAULT 'ANNUAL';

-- Index for performance
CREATE INDEX targets_targetgoal_reporting_frequency_idx 
ON targets_targetgoal(reporting_frequency);
```

---

## 10. Migration Details

### Migration File: `0003_add_reporting_frequency.py`

```python
# Also included department field from earlier work
- Added department FK to TargetGoal
- Added reporting_frequency CharField with choices
- Default value: ANNUAL
- Indexed for query performance
```

---

## 11. Key Benefits

✅ **Multi-year Targets**: Track progress across 2, 5, 10+ years  
✅ **Flexible Reporting**: Switch between DAILY, WEEKLY, MONTHLY, QUARTERLY, ANNUAL  
✅ **Auto-Generation**: Missing periods created automatically  
✅ **Accurate Progress**: Computes across all periods in range  
✅ **Enterprise-Grade**: Supports complex ESG tracking scenarios  

---

## 12. Testing Checklist

- [ ] Create target with QUARTERLY frequency (2025-2028)
- [ ] Verify 16 quarterly periods auto-generated
- [ ] Create target with ANNUAL frequency (2020-2030)
- [ ] Verify 11 annual periods auto-generated
- [ ] Update target reporting_frequency from MONTHLY to QUARTERLY
- [ ] Verify progress computation uses all periods
- [ ] Test with missing baseline year data
- [ ] Test with partial period data (some quarters missing submissions)
- [ ] Verify period generation doesn't create duplicates
- [ ] Test error handling for invalid frequency

---

## 13. Code References

**Model**: `src/targets/models/target_goal.py`  
**Selector**: `src/targets/selectors/reporting_periods.py`  
**Service**: `src/targets/services/reporting_period_service.py`  
**Serializers**: `src/targets/api/serializers.py`  
**Views**: `src/targets/api/views.py`  
**Migration**: `src/targets/migrations/0003_add_reporting_frequency.py`  
