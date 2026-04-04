# Quick Start: Activity Management API

## Overview
The activity management API provides 21 REST endpoints for managing environmental activities, submissions, and analytics.

## Base Path
```
/api/v1/activities/
```

## Quick Examples

### 1. List All Activity Types
```bash
curl -X GET http://localhost:8000/api/v1/activities/types/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

**Response:**
```json
{
  "status": "success",
  "data": [
    {
      "id": "uuid",
      "name": "Electricity Consumption",
      "unit": "kWh",
      "scope": {
        "code": "SCOPE_2",
        "name": "Energy Indirect Emissions"
      },
      "indicator": {
        "id": "uuid",
        "code": "GHG002",
        "name": "Scope 2 Emissions",
        "collection_method": "activity"
      },
      
      "is_active": true
    }
  ]
}
```

### 2. Create Activity Submission
```bash
curl -X POST http://localhost:8000/api/v1/activities/submissions/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "X-ORG-ID: your-org-uuid" \
  -H "Content-Type: application/json" \
  -H "X-CSRFToken: YOUR_CSRF_TOKEN" \
  -d '{
    "activity_type_id": "activity-type-uuid",
    "reporting_period_id": "period-uuid",
    "facility_id": "facility-uuid",
    "value": 1234.56,
    "unit": "kWh"
  }'
```

### 3. Get Period Submissions with Aggregations
```bash
curl -X GET "http://localhost:8000/api/v1/activities/submissions/period/{period_id}/" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "X-ORG-ID: your-org-uuid"
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "period": {
      "id": "uuid",
      "year": 2024,
      "quarter": "Q1",
      "status": "open"
    },
    "summary": {
      "total_submissions": 45,
      "total_value": 125000.50,
      "by_scope": [
        {
          "scope": "SCOPE_1",
          "count": 20,
          "total_value": 50000.00
        }
      ]
    },
    "submissions": [...]
  }
}
```

### 4. Get Analytics Summary
```bash
curl -X GET "http://localhost:8000/api/v1/activities/analytics/summary/?start_date=2024-01-01&end_date=2024-12-31" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "X-ORG-ID: your-org-uuid"
```

### 5. Bulk Create Submissions
```bash
curl -X POST http://localhost:8000/api/v1/activities/submissions/bulk/create/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "X-ORG-ID: your-org-uuid" \
  -H "Content-Type: application/json" \
  -H "X-CSRFToken: YOUR_CSRF_TOKEN" \
  -d '{
    "submissions": [
      {
        "activity_type_id": "uuid1",
        "reporting_period_id": "period-uuid",
        "value": 100.00,
        "unit": "kWh"
      },
      {
        "activity_type_id": "uuid2",
        "reporting_period_id": "period-uuid",
        "value": 200.00,
        "unit": "kg"
      }
    ]
  }'
```

## Common Filters

### Activity Types
```
?scope=SCOPE_1              # Filter by scope
 
?is_active=true             # Only active types
?has_indicator=true         # Only types with indicators
?search=electricity         # Search in name/description
```

### Submissions
```
?reporting_period_id=uuid   # Filter by period
?activity_type_id=uuid      # Filter by activity type
?facility_id=uuid           # Filter by facility
?scope=SCOPE_1              # Filter by scope
?created_by_id=uuid         # Filter by creator
```

### Analytics
```
?start_date=2024-01-01      # From date
?end_date=2024-12-31        # To date
?scope=SCOPE_1              # By scope
?activity_type_id=uuid      # By activity type
?facility_id=uuid           # By facility
```

## Required Headers

### All Requests
```
Authorization: Bearer <JWT_TOKEN>
```

### Organization-Scoped Requests (submissions, analytics)
```
X-ORG-ID: <organization-uuid>
```

### Mutation Requests (POST, PATCH, DELETE)
```
X-CSRFToken: <64-char-masked-token>
Content-Type: application/json
```

## Capabilities Required

| Endpoint Group | Capability |
|----------------|------------|
| List activity types/scopes | None (read-only) |
| Create/update/delete types/scopes | `manage_activity_types` |
| All submission endpoints | `submit_activity` |
| All analytics endpoints | `submit_activity` |

## Response Format

### Success
```json
{
  "status": "success",
  "data": {...}
}
```

### Error
```json
{
  "status": "error",
  "message": "Error description",
  "errors": {...}
}
```

## Integration with Indicators

When you create or update an activity submission:
1. The submission is saved
2. If the activity type is linked to an indicator
3. The indicator value is automatically recalculated
4. The `IndicatorValue` model is updated with aggregated data

This means:
- ✅ Activities automatically feed into ESG metrics
- ✅ Targets can reference calculated indicator values
- ✅ No manual indicator submission needed for activity-based metrics

## Next Steps

1. **Map Activities to Indicators**: Use Django admin or create mappings via API
2. **Test End-to-End Flow**: Submit activity → Check indicator value → Verify targets
3. **Backfill Data**: Run `python manage.py backfill_indicator_values` for historical data
4. **Add Capabilities**: Ensure users have `submit_activity` and `manage_activity_types` capabilities

## Full Documentation

See [ACTIVITY_API_ENDPOINTS.md](./ACTIVITY_API_ENDPOINTS.md) for complete API reference.
