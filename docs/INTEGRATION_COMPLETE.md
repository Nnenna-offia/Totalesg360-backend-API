# Activity-Indicator Integration - Completion Summary

## ✅ Step 1: Migrations Applied Successfully

All database migrations have been applied:

```
✓ activities.0002_activitytype_indicator
✓ indicators.0004_indicator_collection_method  
✓ indicators.0005_indicatorvalue
```

### What Changed:
- **ActivityType** now has `indicator` FK field (nullable)
- **Indicator** now has `collection_method` field (activity/direct)
- **IndicatorValue** model created to store calculated values

## 📋 Step 2: Map Activities to Indicators

Current status from database query:
- **20 ActivityTypes** exist (all unmapped)
- **12 Indicators** exist (all set to 'direct' collection)

### Manual Mapping Example

Use Django shell or admin to map activities to indicators:

```python
from activities.models import ActivityType
from indicators.models import Indicator

# 1. Get an indicator and set it to activity-based
indicator = Indicator.objects.get(code='GHG001')
indicator.collection_method = Indicator.CollectionMethod.ACTIVITY
indicator.save()

# 2. Link activity types to this indicator
activity_type = ActivityType.objects.get(name='Diesel Combustion')
activity_type.indicator = indicator
activity_type.save()
```

### Automated Mapping

The `map_activities_to_indicators` command supports keyword-based matching:

```bash
# Dry run first
python manage.py map_activities_to_indicators --auto --dry-run

# Apply mappings
python manage.py map_activities_to_indicators --auto
```

## 🔄 Step 3: Backfill Indicator Values

Once activities are mapped, recalculate indicator values from existing submissions:

```bash
# For a specific organization
python manage.py backfill_indicator_values --org-id <uuid>

# For all organizations
python manage.py backfill_indicator_values --all

# Dry run to preview
python manage.py backfill_indicator_values --all --dry-run
```

## 🎯 Step 4: Test the Integration

### Create a Test Submission

```bash
POST /api/v1/activities/submissions/
{
  "activity_type_id": "<mapped-activity-uuid>",
  "reporting_period_id": "<period-uuid>",
  "facility_id": "<facility-uuid>",
  "value": 100.0,
  "unit": "kg"
}
```

**What happens:**
1. ✓ ActivitySubmission created
2. ✓ Emission calculation triggered (if applicable)
3. ✓ `update_indicator_value()` called automatically
4. ✓ IndicatorValue updated with aggregated sum

### Verify Indicator Values

Query the calculated values:

```python
from indicators.models import IndicatorValue

values = IndicatorValue.objects.filter(
    organization=org,
    indicator__code='GHG001',
    reporting_period=period
)

for val in values:
    print(f"{val.facility}: {val.value}")
    print(f"  Activities: {val.metadata['activity_count']}")
```

### Test Direct Submission Block

Try submitting an activity-based indicator directly:

```bash
POST /api/v1/submissions/submit/
{
  "indicator_id": "<activity-indicator-uuid>",
  ...
}
```

**Expected:** 400 Bad Request
```json
{
  "detail": "This indicator is activity-derived and cannot be submitted directly. Please submit activity data instead."
}
```

## 📊 Architecture Flow

```
User submits activity
    ↓
POST /api/v1/activities/submissions/
    ↓
ActivitySubmission created
    ↓
submit_activity_value() service
    ↓
update_indicator_value() triggered
    ↓
IndicatorValue calculated (SUM of activities)
    ↓
Targets can read from IndicatorValue
    ↓
Dashboard/Compliance use IndicatorValue
```

## 🔧 Next Actions

1. **Map your activities to indicators** (manually or via command)
2. **Set indicators to activity-based** for environmental metrics
3. **Run backfill** if you have existing activity submissions
4. **Test the flow** with a new activity submission
5. **Update dashboards** to read from IndicatorValue for activity-based indicators

## 📖 Documentation

Full guide: [docs/ACTIVITY_INDICATOR_INTEGRATION.md](../docs/ACTIVITY_INDICATOR_INTEGRATION.md)

## 🎓 Example Mapping Recommendations

| Activity Type | Indicator | Collection Method |
|--------------|-----------|-------------------|
| Diesel Combustion | GHG Scope 1 Emissions | activity |
| Electricity Usage | GHG Scope 2 Emissions | activity |
| Waste Disposal | Total Waste Generated | activity |
| Water Pumping | Water Withdrawal | activity |
| Paper Usage | Paper Consumption | activity |
| Employee Training | Training Hours (Social) | direct |
| Board Diversity | Board Composition (Gov) | direct |

**Rule of thumb:**
- **Environmental/Operational data** → activity-based
- **Social/Governance data** → direct submission

---

✅ **Integration Complete!** The system now supports activity-derived indicators alongside direct submissions.
