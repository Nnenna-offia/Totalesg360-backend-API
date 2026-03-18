# Activity-Indicator Integration Guide

## Overview

The system has been refactored so that **environmental indicators are derived from operational activities** rather than being directly submitted. This creates a proper data flow:

```
ActivityType → ActivitySubmission → IndicatorValue → Targets → Compliance/Dashboard
```

## Architecture Changes

### 1. ActivityType → Indicator Relationship

**Model**: `ActivityType` now includes an `indicator` foreign key.

```python
class ActivityType(BaseModel):
    indicator = models.ForeignKey(
        "indicators.Indicator",
        on_delete=models.PROTECT,
        related_name="activity_types"
    )
```

**Purpose**: Each activity type declares which indicator it contributes to.

**Examples**:
- Diesel combustion → Scope 1 emissions
- Electricity usage → Scope 2 emissions
- Waste disposal → Waste generated
- Water pumping → Water withdrawal

### 2. Indicator Collection Method

**Model**: `Indicator` now has a `collection_method` field.

```python
class Indicator(BaseModel):
    class CollectionMethod(models.TextChoices):
        ACTIVITY = "activity", "Activity Based"
        DIRECT = "direct", "Direct Submission"
    
    collection_method = models.CharField(
        max_length=20,
        choices=CollectionMethod.choices,
        default=CollectionMethod.DIRECT
    )
```

**Rules**:
- `ACTIVITY`: Values calculated from activities; direct submission blocked
- `DIRECT`: Values submitted manually through indicator submission endpoint

### 3. IndicatorValue Model

**New model** to store calculated indicator values.

```python
class IndicatorValue(BaseModel):
    organization = ForeignKey("organizations.Organization")
    indicator = ForeignKey("indicators.Indicator")
    reporting_period = ForeignKey("submissions.ReportingPeriod")
    facility = ForeignKey("organizations.Facility", null=True)
    value = FloatField()
    metadata = JSONField()  # Contains calculation details
```

**Purpose**: Stores aggregated values from activities. Updated automatically when activities change.

### 4. Aggregation Service

**Service**: `indicators.services.indicator_aggregation`

**Functions**:
- `update_indicator_value(activity_submission)` - Recalculates indicator after activity change
- `recalculate_all_indicators_for_period(org, period)` - Bulk recalculation

**Triggers**: Called automatically when:
- ActivitySubmission created
- ActivitySubmission updated
- ActivitySubmission deleted

## Workflow

### Submitting Activity Data

```
POST /api/v1/activities/submissions/
{
  "activity_type_id": "<uuid>",
  "reporting_period_id": "<uuid>",
  "facility_id": "<uuid>",
  "value": 123.45,
  "unit": "liters"
}
```

**What happens**:
1. `ActivitySubmission` created
2. Emission calculation triggered (if applicable)
3. `update_indicator_value()` called
4. `IndicatorValue` updated/created with aggregated sum

### Blocked: Direct Indicator Submission

For activity-derived indicators:

```
POST /api/v1/submissions/submit/
{
  "indicator_id": "<activity-indicator-uuid>",
  ...
}
```

**Response**: `400 Bad Request`
```json
{
  "type": "validation-error",
  "title": "Validation error",
  "detail": "This indicator is activity-derived and cannot be submitted directly. Please submit activity data instead."
}
```

### Targets Reference Indicators

Targets continue to reference `Indicator`, not `ActivityType`.

Target progress is calculated from `IndicatorValue` for activity-derived indicators.

Example:
- Target: Reduce Scope 1 Emissions by 20%
- Progress: Compare `IndicatorValue.value` against baseline

## Migration Strategy

### Step 1: Run Migrations

```bash
python manage.py migrate activities
python manage.py migrate indicators
```

Creates:
- `ActivityType.indicator` FK (nullable)
- `Indicator.collection_method` field
- `IndicatorValue` table

### Step 2: Map Activities to Indicators

**Option A: Automatic mapping** (keyword-based):
```bash
python manage.py map_activities_to_indicators --auto
```

**Option B: Manual mapping** (via Django admin or shell):
```python
from activities.models import ActivityType
from indicators.models import Indicator

diesel_activity = ActivityType.objects.get(name="Diesel Combustion")
scope1_indicator = Indicator.objects.get(code="GHG_SCOPE1")

diesel_activity.indicator = scope1_indicator
diesel_activity.save()

# Set indicator to activity-based
scope1_indicator.collection_method = Indicator.CollectionMethod.ACTIVITY
scope1_indicator.save()
```

### Step 3: Backfill Indicator Values

Recalculate all indicator values from existing activities:

```bash
# Single organization
python manage.py backfill_indicator_values --org-id <uuid>

# All organizations
python manage.py backfill_indicator_values --all

# Dry run
python manage.py backfill_indicator_values --all --dry-run
```

### Step 4: Update Dashboard/Compliance Services

Update selectors to read from `IndicatorValue` for activity-derived indicators:

```python
from indicators.models import IndicatorValue

# Old way (direct submission)
submissions = DataSubmission.objects.filter(indicator=indicator, ...)

# New way (activity-derived)
if indicator.collection_method == Indicator.CollectionMethod.ACTIVITY:
    values = IndicatorValue.objects.filter(indicator=indicator, ...)
else:
    submissions = DataSubmission.objects.filter(indicator=indicator, ...)
```

## Permissions

| Action | Capability Required |
|--------|-------------------|
| Submit activity data | `activity.submit` |
| Manage activity types | `activity_type.manage` |
| Submit direct indicators | `indicator.submit` (blocked for activity-derived) |
| View indicator values | `indicator.view` |

## Examples

### Creating Activity-Linked Indicator

```python
# Create indicator
indicator = Indicator.objects.create(
    code="WASTE_GENERATED",
    name="Total Waste Generated",
    pillar=Indicator.Pillar.ENVIRONMENTAL,
    data_type=Indicator.DataType.NUMBER,
    unit="kg",
    collection_method=Indicator.CollectionMethod.ACTIVITY
)

# Create activity type
activity_type = ActivityType.objects.create(
    name="General Waste Disposal",
    unit="kg",
    scope=scope,
    indicator=indicator
)
```

### Submitting Activity

```bash
curl -X POST /api/v1/activities/submissions/ \
  -H "Content-Type: application/json" \
  -H "X-CSRFToken: <token>" \
  -H "X-ORG-ID: <org-id>" \
  --cookie "access=<jwt>" \
  -d '{
    "activity_type_id": "<activity-type-uuid>",
    "reporting_period_id": "<period-uuid>",
    "value": 500.0,
    "unit": "kg"
  }'
```

**Result**: `IndicatorValue` for "WASTE_GENERATED" updated automatically.

### Querying Indicator Values

```python
from indicators.models import IndicatorValue

values = IndicatorValue.objects.filter(
    organization=org,
    indicator__code="WASTE_GENERATED",
    reporting_period=period
)

for val in values:
    print(f"{val.facility}: {val.value} kg")
    print(f"  Based on {val.metadata['activity_count']} activities")
```

## Benefits

1. **Single source of truth**: Activities are operational data; indicators are derived metrics
2. **Data integrity**: No conflicting data from multiple sources
3. **Automatic updates**: Indicator values recalculate when activities change
4. **Audit trail**: Activity submissions provide detailed history
5. **Flexibility**: Mix activity-derived and directly-submitted indicators

## Troubleshooting

### "Indicator not found" on activity submission
- Ensure `ActivityType.indicator` is set
- Check `Indicator.is_active = True`

### Indicator value not updating
- Check `Indicator.collection_method == 'activity'`
- Verify aggregation service didn't error (check logs)
- Run manual recalculation: `python manage.py backfill_indicator_values`

### "Cannot submit directly" error
- Indicator has `collection_method = 'activity'`
- Submit activity data instead of indicator submission
- Or change indicator to `collection_method = 'direct'` if appropriate

## Next Steps

1. Map all environmental indicators to activity-based collection
2. Create activity types for all operational data sources
3. Train users on activity submission workflow
4. Update dashboards to read from `IndicatorValue`
5. Archive old `DataSubmission` records for activity-derived indicators
