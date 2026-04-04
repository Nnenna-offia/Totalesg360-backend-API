# Activity Management API Endpoints

Complete REST API for activity management in the TotalESG360 system.

## Base URL
All endpoints are prefixed with `/api/activities/`

---

## Activity Types

### List/Create Activity Types
**GET** `/api/activities/types/`
- **Description**: List all activity types with optional filtering
- **Query Parameters**:
  - `scope` (string): Filter by scope code
  - `is_active` (boolean): Filter by active status
  - `has_indicator` (boolean): Filter by indicator linkage
  - `search` (string): Search in name and description
- **Response**: Array of activity types with nested scope and indicator data

**POST** `/api/activities/types/`
- **Description**: Create a new activity type
- **Capability Required**: `manage_activity_types`
- **Request Body**:
```json
{
  "name": "Electricity Consumption",
  "description": "Monthly electricity usage across facilities",
  "unit": "kWh",
  "scope": "scope-uuid",
  "indicator": "indicator-uuid",
  "is_active": true
}
```

### Activity Type Detail
**GET** `/api/activities/types/{id}/`
- **Description**: Get detailed activity type information including submission count

**PATCH** `/api/activities/types/{id}/`
- **Description**: Update an activity type
- **Capability Required**: `manage_activity_types`
- **Request Body**: Partial update fields

**DELETE** `/api/activities/types/{id}/`
- **Description**: Delete an activity type (only if no submissions exist)
- **Capability Required**: `manage_activity_types`

---

## Scopes

### List/Create Scopes
**GET** `/api/activities/scopes/`
- **Description**: List all available scopes

**POST** `/api/activities/scopes/`
- **Description**: Create a new scope
- **Capability Required**: `manage_activity_types`
- **Request Body**:
```json
{
  "code": "SCOPE_3",
  "name": "Scope 3 Emissions",
  "description": "Indirect emissions from value chain"
}
```

### Scope Detail
**GET** `/api/activities/scopes/{id}/`
**PATCH** `/api/activities/scopes/{id}/`
**DELETE** `/api/activities/scopes/{id}/`
- **Capability Required**: `manage_activity_types`

---

## Activity Submissions

### Create Submission (Original)
**POST** `/api/activities/submissions/`
- **Description**: Create a single activity submission (backward compatible)
- **Capability Required**: `submit_activity`
- **Headers**: `X-ORG-ID` required
- **Request Body**:
```json
{
  "activity_type_id": "uuid",
  "reporting_period_id": "uuid",
  "facility_id": "uuid",
  "value": 1234.56,
  "unit": "kWh"
}
```

### List Submissions
**GET** `/api/activities/submissions/list/`
- **Description**: List all activity submissions for the organization
- **Capability Required**: `submit_activity`
- **Headers**: `X-ORG-ID` required
- **Query Parameters**:
  - `reporting_period_id` (uuid): Filter by reporting period
  - `activity_type_id` (uuid): Filter by activity type
  - `facility_id` (uuid): Filter by facility
  - `created_by_id` (uuid): Filter by creator
  - `scope` (string): Filter by scope code

### Submission Detail
**GET** `/api/activities/submissions/{id}/`
- **Description**: Get detailed submission information
- **Capability Required**: `submit_activity`
- **Headers**: `X-ORG-ID` required

**PATCH** `/api/activities/submissions/{id}/`
- **Description**: Update submission value or unit (only for draft/open periods)
- **Capability Required**: `submit_activity`
- **Headers**: `X-ORG-ID` required
- **Request Body**:
```json
{
  "value": 2000.00,
  "unit": "kWh"
}
```
- **Note**: Automatically triggers indicator recalculation

**DELETE** `/api/activities/submissions/{id}/`
- **Description**: Delete submission (only for draft/open periods)
- **Capability Required**: `submit_activity`
- **Headers**: `X-ORG-ID` required
- **Note**: Automatically triggers indicator recalculation

### Submissions by Period
**GET** `/api/activities/submissions/period/{period_id}/`
- **Description**: Get all submissions for a specific reporting period with aggregations
- **Capability Required**: `submit_activity`
- **Headers**: `X-ORG-ID` required
- **Query Parameters**:
  - `activity_type_id` (uuid): Filter by activity type
  - `facility_id` (uuid): Filter by facility
  - `scope` (string): Filter by scope code
- **Response**:
```json
{
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
```

---

## Bulk Operations

### Bulk Create Submissions
**POST** `/api/activities/submissions/bulk/create/`
- **Description**: Create multiple submissions in a single request (max 100)
- **Capability Required**: `submit_activity`
- **Headers**: `X-ORG-ID` required
- **Request Body**:
```json
{
  "submissions": [
    {
      "activity_type_id": "uuid",
      "reporting_period_id": "uuid",
      "facility_id": "uuid",
      "value": 1234.56,
      "unit": "kWh"
    },
    ...
  ]
}
```
- **Response**:
```json
{
  "created": [...],
  "created_count": 95,
  "error_count": 5,
  "errors": [
    {
      "index": 3,
      "data": {...},
      "errors": {...}
    }
  ]
}
```

### Bulk Delete Submissions
**POST** `/api/activities/submissions/bulk/delete/`
- **Description**: Delete multiple submissions (max 100)
- **Capability Required**: `submit_activity`
- **Headers**: `X-ORG-ID` required
- **Request Body**:
```json
{
  "submission_ids": ["uuid1", "uuid2", ...]
}
```
- **Response**:
```json
{
  "deleted_count": 90,
  "requested_count": 100,
  "locked_count": 10,
  "locked_submissions": [
    {
      "id": "uuid",
      "reason": "Period is submitted"
    }
  ]
}
```

---

## Analytics

### Summary Analytics
**GET** `/api/activities/analytics/summary/`
- **Description**: Get overall activity submission analytics
- **Capability Required**: `submit_activity`
- **Headers**: `X-ORG-ID` required
- **Query Parameters**:
  - `start_date` (date): Filter from date
  - `end_date` (date): Filter to date
  - `scope` (string): Filter by scope code
- **Response**:
```json
{
  "overall": {
    "total_submissions": 1250,
    "total_value": 500000.00,
    "avg_value": 400.00,
    "unique_activity_types": 15,
    "unique_facilities": 8
  },
  "by_activity_type": [...],
  "by_scope": [...],
  "by_facility": [...]
}
```

### Trends Analytics
**GET** `/api/activities/analytics/trends/`
- **Description**: Get time-series trends grouped by month
- **Capability Required**: `submit_activity`
- **Headers**: `X-ORG-ID` required
- **Query Parameters**:
  - `activity_type_id` (uuid): Filter by activity type
  - `scope` (string): Filter by scope code
  - `facility_id` (uuid): Filter by facility
- **Response**:
```json
{
  "trends": [
    {
      "month": "2024-01",
      "submission_count": 45,
      "total_value": 12500.00,
      "avg_value": 277.78
    },
    ...
  ]
}
```

### Facility Analytics
**GET** `/api/activities/analytics/by-facility/`
- **Description**: Get detailed breakdown by facility with scope aggregations
- **Capability Required**: `submit_activity`
- **Headers**: `X-ORG-ID` required
- **Query Parameters**:
  - `reporting_period_id` (uuid): Filter by reporting period
  - `scope` (string): Filter by scope code
- **Response**:
```json
{
  "facilities": [
    {
      "facility": {
        "id": "uuid",
        "name": "Main Plant",
        "location": "New York"
      },
      "totals": {
        "submission_count": 120,
        "total_value": 50000.00,
        "unique_activity_types": 8
      },
      "by_scope": [
        {
          "scope": "SCOPE_1",
          "scope_name": "Direct Emissions",
          "submission_count": 60,
          "total_value": 30000.00
        }
      ]
    }
  ]
}
```

### Period Comparison Analytics
**GET** `/api/activities/analytics/comparison/`
- **Description**: Compare submissions across reporting periods
- **Capability Required**: `submit_activity`
- **Headers**: `X-ORG-ID` required
- **Query Parameters**:
  - `activity_type_id` (uuid): Filter by activity type
  - `scope` (string): Filter by scope code
- **Response**:
```json
{
  "comparison": [
    {
      "period": {
        "id": "uuid",
        "year": 2024,
        "quarter": "Q1"
      },
      "submission_count": 45,
      "total_value": 12500.00,
      "avg_value": 277.78,
      "unique_activity_types": 10
    },
    ...
  ]
}
```

---

## Capabilities Required

| Capability | Description | Endpoints |
|------------|-------------|-----------|
| `submit_activity` | Submit and manage activity data | All submission and analytics endpoints |
| `manage_activity_types` | Manage activity type catalog | Activity types and scopes create/update/delete |

---

## Response Format

All endpoints follow the standard API response format:

### Success Response
```json
{
  "status": "success",
  "data": {...}
}
```

### Error Response
```json
{
  "status": "error",
  "message": "Error description",
  "errors": {...}
}
```

---

## Notes

1. **Organization Context**: Most endpoints require `X-ORG-ID` header for organization scoping
2. **Period Locking**: Submissions can only be modified/deleted for periods with status `draft` or `open`
3. **Indicator Recalculation**: Updates and deletes automatically trigger indicator value recalculation
4. **Bulk Operations**: Limited to 100 items per request for performance
5. **Filtering**: Most list endpoints support multiple filter combinations
6. **Pagination**: Not yet implemented (to be added for large datasets)
