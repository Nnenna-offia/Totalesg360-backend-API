# Activities API Endpoints & Payloads

## Base URL
```
/api/v1/activities/
```

---

## 1. Activity Types Management

### 1.1 List Activity Types

**Endpoint:**
```
GET /api/v1/activities/types/
```

**Authentication:** Required (IsAuthenticated)  
**Permissions:** None required (public catalog)

**Query Parameters:**
```
- scope: Filter by scope code (e.g., "emissions", "waste")
- is_active: Filter by active status (true/false)
- has_indicator: Filter by linked indicator (true/false)
- search: Search in name and description
```

**Example Request:**
```http
GET /api/v1/activities/types/?scope=emissions&is_active=true
```

**Response:** `200 OK`
```json
{
  "success": true,
  "data": [
    {
      "id": "type-uuid-1",
      "name": "CO2 Emissions",
      "unit": "tonnes",
      "scope": {
        "id": "scope-uuid",
        "code": "emissions",
        "name": "Emissions",
        "description": "Greenhouse gas emissions"
      },
      "indicator": {
        "id": "ind-uuid",
        "code": "GHG-001",
        "name": "Total GHG Emissions",
        "collection_method": "activity"
      },
      "is_active": true,
      "created_at": "2026-03-28T10:00:00Z",
      "updated_at": "2026-03-28T10:00:00Z"
    }
  ]
}
```

---

### 1.2 Create Activity Type

**Endpoint:**
```
POST /api/v1/activities/types/
```

**Authentication:** Required  
**Permissions:** Required - `manage_activity_types` capability

**Request Body:**
```json
{
  "name": "CO2 Emissions",
  "description": "Scope 1 direct emissions from fossil fuels",
  "unit": "tonnes",
  "scope": "scope-uuid",
  "indicator": "indicator-uuid",
  "is_active": true
}
```

**Response:** `201 Created`
```json
{
  "success": true,
  "data": {
    "id": "type-uuid",
    "name": "CO2 Emissions",
    "description": "Scope 1 direct emissions from fossil fuels",
    "unit": "tonnes",
    "scope": {
      "id": "scope-uuid",
      "code": "emissions",
      "name": "Emissions"
    },
    "indicator": {
      "id": "indicator-uuid",
      "code": "GHG-001",
      "name": "Total GHG Emissions",
      "pillar": "climate",
      "data_type": "numeric",
      "collection_method": "activity"
    },
    "is_active": true,
    "submission_count": 0,
    "created_at": "2026-03-28T10:00:00Z",
    "updated_at": "2026-03-28T10:00:00Z"
  }
}
```

---

### 1.3 Get Activity Type Detail

**Endpoint:**
```
GET /api/v1/activities/types/{type_id}/
```

**Authentication:** Required  
**Permissions:** None required

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "id": "type-uuid",
    "name": "CO2 Emissions",
    "description": "Scope 1 direct emissions",
    "unit": "tonnes",
    "scope": {
      "id": "scope-uuid",
      "code": "emissions",
      "name": "Emissions",
      "description": "Greenhouse gas emissions"
    },
    "indicator": {
      "id": "ind-uuid",
      "code": "GHG-001",
      "name": "Total GHG Emissions",
      "pillar": "climate",
      "data_type": "numeric",
      "collection_method": "activity"
    },
    "is_active": true,
    "submission_count": 45,
    "created_at": "2026-03-28T10:00:00Z",
    "updated_at": "2026-03-28T10:00:00Z"
  }
}
```

---

### 1.4 Update Activity Type

**Endpoint:**
```
PATCH /api/v1/activities/types/{type_id}/
```

**Authentication:** Required  
**Permissions:** Required - `manage_activity_types` capability

**Request Body:**
```json
{
  "name": "CO2 Emissions (Updated)",
  "is_active": false
}
```

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "id": "type-uuid",
    "name": "CO2 Emissions (Updated)",
    "is_active": false,
    ...
  }
}
```

---

### 1.5 Delete Activity Type

**Endpoint:**
```
DELETE /api/v1/activities/types/{type_id}/
```

**Authentication:** Required  
**Permissions:** Required - `manage_activity_types` capability

**Response:** `204 No Content`

---

## 2. Scopes Management

### 2.1 List Scopes

**Endpoint:**
```
GET /api/v1/activities/scopes/
```

**Authentication:** Required  
**Permissions:** None required

**Response:** `200 OK`
```json
{
  "success": true,
  "data": [
    {
      "id": "scope-uuid",
      "code": "emissions",
      "name": "Emissions",
      "description": "Greenhouse gas emissions scope",
      "created_at": "2026-03-28T10:00:00Z",
      "updated_at": "2026-03-28T10:00:00Z"
    },
    {
      "id": "scope-uuid-2",
      "code": "waste",
      "name": "Waste",
      "description": "Waste management activities"
    }
  ]
}
```

---

### 2.2 Create Scope

**Endpoint:**
```
POST /api/v1/activities/scopes/
```

**Authentication:** Required  
**Permissions:** Required - `manage_activity_types` capability

**Request Body:**
```json
{
  "code": "water",
  "name": "Water",
  "description": "Water consumption and management"
}
```

**Response:** `201 Created`
```json
{
  "success": true,
  "data": {
    "id": "scope-uuid",
    "code": "water",
    "name": "Water",
    "description": "Water consumption and management",
    "created_at": "2026-03-28T10:00:00Z",
    "updated_at": "2026-03-28T10:00:00Z"
  }
}
```

---

### 2.3 Get Scope Detail

**Endpoint:**
```
GET /api/v1/activities/scopes/{scope_id}/
```

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "id": "scope-uuid",
    "code": "emissions",
    "name": "Emissions",
    "description": "Greenhouse gas emissions scope",
    "created_at": "2026-03-28T10:00:00Z",
    "updated_at": "2026-03-28T10:00:00Z"
  }
}
```

---

### 2.4 Update Scope

**Endpoint:**
```
PATCH /api/v1/activities/scopes/{scope_id}/
```

**Permissions:** Required - `manage_activity_types` capability

**Request Body:**
```json
{
  "description": "Updated description"
}
```

**Response:** `200 OK`

---

### 2.5 Delete Scope

**Endpoint:**
```
DELETE /api/v1/activities/scopes/{scope_id}/
```

**Permissions:** Required - `manage_activity_types` capability

**Response:** `204 No Content`

---

## 3. Activity Submissions

### 3.1 Create Activity Submission

**Endpoint:**
```
POST /api/v1/activities/submissions/
```

**Authentication:** Required  
**Permissions:** Required - `submit_activity` capability

**Headers:**
```
X-ORG-ID: organization-uuid
```

**Request Body:**
```json
{
  "activity_type_id": "type-uuid",
  "reporting_period_id": "period-uuid",
  "facility_id": "facility-uuid",
  "value": 125.50,
  "unit": "tonnes"
}
```

**Response:** `201 Created`
```json
{
  "success": true,
  "data": {
    "id": "submission-uuid",
    "organization": {
      "id": "org-uuid",
      "name": "My Company"
    },
    "facility": {
      "id": "facility-uuid",
      "name": "Main Factory"
    },
    "activity_type": {
      "id": "type-uuid",
      "name": "CO2 Emissions",
      "unit": "tonnes",
      "scope": {
        "id": "scope-uuid",
        "code": "emissions",
        "name": "Emissions"
      },
      "indicator": {
        "id": "ind-uuid",
        "code": "GHG-001",
        "name": "Total GHG Emissions",
        "collection_method": "activity"
      }
    },
    "reporting_period": {
      "id": "period-uuid",
      "name": "Q1 2026",
      "period_type": "QUARTERLY",
      "status": "OPEN"
    },
    "value": 125.50,
    "unit": "tonnes",
    "created_by": {
      "id": "user-uuid",
      "email": "user@example.com"
    },
    "created_at": "2026-03-28T10:00:00Z",
    "updated_at": "2026-03-28T10:00:00Z"
  }
}
```

---

### 3.2 List Activity Submissions

**Endpoint:**
```
GET /api/v1/activities/submissions/list/
```

**Authentication:** Required  
**Permissions:** Required - `submit_activity` capability

**Headers:**
```
X-ORG-ID: organization-uuid
```

**Query Parameters:**
```
- reporting_period_id: Filter by reporting period
- activity_type_id: Filter by activity type
- facility_id: Filter by facility
- created_by_id: Filter by creator
- scope: Filter by scope code
```

**Example Request:**
```http
GET /api/v1/activities/submissions/list/?reporting_period_id=period-uuid&scope=emissions
```

**Response:** `200 OK`
```json
{
  "success": true,
  "data": [
    {
      "id": "submission-uuid",
      "organization": {
        "id": "org-uuid",
        "name": "My Company"
      },
      "facility": {
        "id": "facility-uuid",
        "name": "Main Factory"
      },
      "activity_type": { ... },
      "reporting_period": { ... },
      "value": 125.50,
      "unit": "tonnes",
      "created_by": { ... },
      "created_at": "2026-03-28T10:00:00Z",
      "updated_at": "2026-03-28T10:00:00Z"
    }
  ]
}
```

---

### 3.3 Get Activity Submission Detail

**Endpoint:**
```
GET /api/v1/activities/submissions/{submission_id}/
```

**Authentication:** Required  
**Permissions:** Required - `submit_activity` capability

**Headers:**
```
X-ORG-ID: organization-uuid
```

**Response:** `200 OK` (same as list item)

---

### 3.4 Update Activity Submission

**Endpoint:**
```
PATCH /api/v1/activities/submissions/{submission_id}/
```

**Authentication:** Required  
**Permissions:** Required - `submit_activity` capability

**Headers:**
```
X-ORG-ID: organization-uuid
```

**Request Body:**
```json
{
  "value": 150.75,
  "unit": "tonnes"
}
```

**Note:** Only `value` and `unit` can be updated. Reporting period must be in OPEN status.

**Response:** `200 OK`
```json
{
  "success": true,
  "data": { ... updated submission ... }
}
```

---

### 3.5 Delete Activity Submission

**Endpoint:**
```
DELETE /api/v1/activities/submissions/{submission_id}/
```

**Authentication:** Required  
**Permissions:** Required - `submit_activity` capability

**Headers:**
```
X-ORG-ID: organization-uuid
```

**Note:** Reporting period must be in OPEN status.

**Response:** `204 No Content`

---

### 3.6 Get Submissions by Reporting Period

**Endpoint:**
```
GET /api/v1/activities/submissions/period/{period_id}/
```

**Authentication:** Required  
**Permissions:** Required - `submit_activity` capability

**Headers:**
```
X-ORG-ID: organization-uuid
```

**Response:** `200 OK`
```json
{
  "success": true,
  "data": [
    { ... submission 1 ... },
    { ... submission 2 ... }
  ]
}
```

---

## 4. Bulk Operations

### 4.1 Bulk Create Activity Submissions

**Endpoint:**
```
POST /api/v1/activities/submissions/bulk/create/
```

**Authentication:** Required  
**Permissions:** Required - `submit_activity` capability

**Headers:**
```
X-ORG-ID: organization-uuid
```

**Request Body:**
```json
{
  "submissions": [
    {
      "activity_type_id": "type-uuid-1",
      "reporting_period_id": "period-uuid",
      "facility_id": "facility-uuid-1",
      "value": 100.0,
      "unit": "tonnes"
    },
    {
      "activity_type_id": "type-uuid-2",
      "reporting_period_id": "period-uuid",
      "facility_id": "facility-uuid-2",
      "value": 50.5,
      "unit": "tonnes"
    }
  ]
}
```

**Response:** `201 Created`
```json
{
  "success": true,
  "data": {
    "created": 2,
    "failed": 0,
    "submissions": [
      { ... submission 1 ... },
      { ... submission 2 ... }
    ],
    "errors": []
  }
}
```

---

### 4.2 Bulk Delete Activity Submissions

**Endpoint:**
```
POST /api/v1/activities/submissions/bulk/delete/
```

**Authentication:** Required  
**Permissions:** Required - `submit_activity` capability

**Headers:**
```
X-ORG-ID: organization-uuid
```

**Request Body:**
```json
{
  "submission_ids": [
    "submission-uuid-1",
    "submission-uuid-2",
    "submission-uuid-3"
  ]
}
```

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "deleted": 3,
    "failed": 0,
    "errors": []
  }
}
```

---

## 5. Analytics

### 5.1 Activity Analytics Summary

**Endpoint:**
```
GET /api/v1/activities/analytics/summary/
```

**Authentication:** Required  
**Permissions:** Required - `submit_activity` capability

**Headers:**
```
X-ORG-ID: organization-uuid
```

**Query Parameters:**
```
- reporting_period_id: Filter to specific period
- scope: Filter by scope code
- start_date: Start date (YYYY-MM-DD)
- end_date: End date (YYYY-MM-DD)
```

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "total_submissions": 150,
    "period_coverage": 95.5,
    "by_scope": [
      {
        "scope": "emissions",
        "count": 80,
        "total_value": 10500.50,
        "unit": "tonnes"
      },
      {
        "scope": "waste",
        "count": 70,
        "total_value": 5200.25,
        "unit": "tonnes"
      }
    ],
    "by_facility": [
      {
        "facility_id": "facility-uuid",
        "facility_name": "Main Factory",
        "submission_count": 85,
        "total_value": 8500.0
      }
    ]
  }
}
```

---

### 5.2 Activity Trends

**Endpoint:**
```
GET /api/v1/activities/analytics/trends/
```

**Authentication:** Required  
**Permissions:** Required - `submit_activity` capability

**Headers:**
```
X-ORG-ID: organization-uuid
```

**Query Parameters:**
```
- activity_type_id: Specific activity type
- scope: Filter by scope code
- granularity: daily|weekly|monthly|quarterly (default: monthly)
- months: Number of months to include (default: 12)
```

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "activity_type": "CO2 Emissions",
    "granularity": "monthly",
    "trends": [
      {
        "period": "2025-12",
        "value": 950.50,
        "submission_count": 15,
        "change_percent": 2.5
      },
      {
        "period": "2026-01",
        "value": 975.75,
        "submission_count": 18,
        "change_percent": 2.65
      },
      {
        "period": "2026-02",
        "value": 1000.25,
        "submission_count": 20,
        "change_percent": 2.51
      }
    ]
  }
}
```

---

### 5.3 Analytics by Facility

**Endpoint:**
```
GET /api/v1/activities/analytics/by-facility/
```

**Authentication:** Required  
**Permissions:** Required - `submit_activity` capability

**Headers:**
```
X-ORG-ID: organization-uuid
```

**Query Parameters:**
```
- reporting_period_id: Filter to specific period
- scope: Filter by scope code
- sort_by: value|count (default: value)
```

**Response:** `200 OK`
```json
{
  "success": true,
  "data": [
    {
      "facility_id": "facility-uuid-1",
      "facility_name": "Main Factory",
      "submission_count": 45,
      "by_scope": [
        {
          "scope": "emissions",
          "count": 25,
          "total_value": 5000.0,
          "unit": "tonnes"
        },
        {
          "scope": "waste",
          "count": 20,
          "total_value": 2500.0,
          "unit": "tonnes"
        }
      ]
    },
    {
      "facility_id": "facility-uuid-2",
      "facility_name": "Warehouse",
      "submission_count": 30,
      "by_scope": [
        {
          "scope": "emissions",
          "count": 18,
          "total_value": 3500.50,
          "unit": "tonnes"
        }
      ]
    }
  ]
}
```

---

### 5.4 Analytics Comparison

**Endpoint:**
```
GET /api/v1/activities/analytics/comparison/
```

**Authentication:** Required  
**Permissions:** Required - `submit_activity` capability

**Headers:**
```
X-ORG-ID: organization-uuid
```

**Query Parameters:**
```
- period_1: First period ID
- period_2: Second period ID
- scope: Filter by scope code
```

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "period_1": {
      "id": "period-uuid-1",
      "name": "Q4 2025",
      "total_submissions": 100,
      "total_value": 8500.0
    },
    "period_2": {
      "id": "period-uuid-2",
      "name": "Q1 2026",
      "total_submissions": 110,
      "total_value": 9200.0
    },
    "comparison": {
      "submission_change": 10,
      "submission_change_percent": 10.0,
      "value_change": 700.0,
      "value_change_percent": 8.24,
      "by_scope": [
        {
          "scope": "emissions",
          "period_1_value": 5000.0,
          "period_2_value": 5500.0,
          "change_percent": 10.0
        }
      ]
    }
  }
}
```

---

## Error Responses

All endpoints follow RFC 7807 problem detail format:

### 400 Bad Request
```json
{
  "type": "https://api.example.com/problems/validation-error",
  "title": "Validation Error",
  "detail": "Invalid field value",
  "code": "validation_error",
  "errors": {
    "value": ["Must be a positive number"]
  }
}
```

### 403 Forbidden
```json
{
  "type": "https://api.example.com/problems/forbidden",
  "title": "Forbidden",
  "detail": "You don't have permission to submit activities",
  "code": "permission_denied"
}
```

### 404 Not Found
```json
{
  "type": "https://api.example.com/problems/not-found",
  "title": "Not Found",
  "detail": "Activity submission not found",
  "code": "not_found"
}
```

### 500 Internal Server Error
```json
{
  "type": "https://api.example.com/problems/internal-server-error",
  "title": "Internal Server Error",
  "detail": "An unexpected error occurred",
  "code": "internal_error"
}
```

---

## Authentication Headers

All authenticated endpoints require:

```
Authorization: Bearer <access_token>
```

Or use HttpOnly cookies:
- `access_token` (set via login)
- `csrf_token` (for POST/PATCH/DELETE requests)

---

## Headers Required

**All endpoints require organization context:**
```
X-ORG-ID: organization-uuid
```

**For POST/PATCH/DELETE with CSRF protection:**
```
X-CSRFToken: <csrf_token_value>
Referer: https://your-domain.com
```

---

## Pagination

Endpoints that return lists may support pagination via query params:
```
- page: Page number (default: 1)
- page_size: Items per page (default: 20, max: 100)
```

Example:
```
GET /api/v1/activities/submissions/list/?page=2&page_size=50
```

---

## Status Codes Reference

| Code | Meaning |
|------|---------|
| 200 | Success (GET, PATCH) |
| 201 | Created (POST) |
| 204 | No Content (DELETE) |
| 400 | Bad Request (validation error) |
| 403 | Forbidden (permission denied) |
| 404 | Not Found |
| 500 | Internal Server Error |
