# ReportingPeriod Refactor - API Usage Guide

## Overview

The ReportingPeriod model has been refactored to support enterprise-grade ESG reporting with flexible date-based periods instead of the previous year/quarter limitation.

## What Changed

### Before (Old Schema)
```json
{
  "year": 2025,
  "quarter": 1,
  "status": "OPEN"
}
```

### After (New Schema)
```json
{
  "name": "Q1 2025",
  "period_type": "QUARTERLY",
  "start_date": "2025-01-01",
  "end_date": "2025-03-31",
  "status": "OPEN"
}
```

---

## Supported Period Types

1. **DAILY** - Daily reporting (e.g., sensor data, energy consumption)
2. **WEEKLY** - Weekly reporting (e.g., safety incidents, waste management)
3. **BI_WEEKLY** - Bi-weekly reporting (e.g., maintenance checks)
4. **MONTHLY** - Monthly reporting (e.g., sustainability reporting)
5. **QUARTERLY** - Quarterly reporting (e.g., executive ESG review)
6. **SEMI_ANNUAL** - Semi-annual reporting (H1, H2)
7. **ANNUAL** - Annual reporting (e.g., regulatory submissions)
8. **CUSTOM** - Custom date ranges (e.g., project-based reporting)

---

## API Endpoints

### 1. Create Reporting Period

**POST** `/api/v1/submissions/periods/`

**Headers:**
```
X-ORG-ID: <organization-uuid>
X-CSRFToken: <csrf-token>
Content-Type: application/json
```

**Request Body Examples:**

#### Quarterly Period
```json
{
  "name": "Q1 2025",
  "period_type": "QUARTERLY",
  "start_date": "2025-01-01",
  "end_date": "2025-03-31"
}
```

#### Monthly Period
```json
{
  "name": "Jan 2025",
  "period_type": "MONTHLY",
  "start_date": "2025-01-01",
  "end_date": "2025-01-31"
}
```

#### Weekly Period
```json
{
  "name": "Week 1 2025",
  "period_type": "WEEKLY",
  "start_date": "2025-01-01",
  "end_date": "2025-01-07"
}
```

#### Custom Period (Project-based)
```json
{
  "name": "Project Phase 1",
  "period_type": "CUSTOM",
  "start_date": "2025-03-15",
  "end_date": "2025-09-30"
}
```

**Success Response (201 Created):**
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "organization": "uuid",
    "name": "Q1 2025",
    "period_type": "QUARTERLY",
    "start_date": "2025-01-01",
    "end_date": "2025-03-31",
    "status": "OPEN",
    "opened_at": "2025-01-01T00:00:00Z",
    "locked_at": null,
    "is_active": true
  }
}
```

**Error Response - Duplicate Period (400):**
```json
{
  "type": "https://dev-backend.totalesg360.com/problems/duplicate-period",
  "title": "Duplicate reporting period",
  "status": 400,
  "detail": "A reporting period named 'Q1 2025' already exists for this organization.",
  "instance": "/api/v1/submissions/periods/"
}
```

**Error Response - Validation Error (400):**
```json
{
  "type": "https://dev-backend.totalesg360.com/problems/invalid-request",
  "title": "Invalid payload",
  "status": 400,
  "detail": {
    "start_date": ["start_date must be before end_date"]
  },
  "instance": "/api/v1/submissions/periods/"
}
```

---

### 2. List Reporting Periods

**GET** `/api/v1/submissions/periods/`

**Headers:**
```
X-ORG-ID: <organization-uuid>
```

**Success Response (200 OK):**
```json
{
  "success": true,
  "data": [
    {
      "id": "uuid",
      "organization": "uuid",
      "name": "Q1 2025",
      "period_type": "QUARTERLY",
      "start_date": "2025-01-01",
      "end_date": "2025-03-31",
      "status": "OPEN",
      "opened_at": "2025-01-01T00:00:00Z",
      "locked_at": null,
      "is_active": true
    },
    {
      "id": "uuid",
      "organization": "uuid",
      "name": "Jan 2025",
      "period_type": "MONTHLY",
      "start_date": "2025-01-01",
      "end_date": "2025-01-31",
      "status": "LOCKED",
      "opened_at": "2025-01-01T00:00:00Z",
      "locked_at": "2025-02-01T10:30:00Z",
      "is_active": true
    }
  ],
  "meta": {
    "count": 2,
    "page_size": 20,
    "current_page": 1
  }
}
```

---

## Python Service Usage

### Auto-Generate Periods for a Year

```python
from submissions.services.period_generation import generate_reporting_periods
from organizations.models import Organization

# Get your organization
org = Organization.objects.get(name="Your Company")

# Generate all quarterly periods for 2025
periods = generate_reporting_periods(
    organization=org,
    year=2025,
    period_types=["QUARTERLY"],
    save=True
)

# Result: Creates Q1 2025, Q2 2025, Q3 2025, Q4 2025
```

### Generate Multiple Period Types

```python
# Generate monthly, quarterly, and annual periods for 2025
periods = generate_reporting_periods(
    organization=org,
    year=2025,
    period_types=["MONTHLY", "QUARTERLY", "ANNUAL"],
    save=True
)

# Result:
# - 12 monthly periods (Jan 2025 - Dec 2025)
# - 4 quarterly periods (Q1 2025 - Q4 2025)
# - 1 annual period (2025)
```

### Generate Weekly Periods

```python
# Generate 52 weekly periods for 2025
periods = generate_reporting_periods(
    organization=org,
    year=2025,
    period_types=["WEEKLY"],
    save=True
)

# Result: Week 1 2025, Week 2 2025, ..., Week 52 2025
```

### Create Custom Period

```python
from submissions.services.period_generation import generate_custom_period
from datetime import date

# Create a custom period for a specific project
period = generate_custom_period(
    organization=org,
    name="Sustainability Project Q1-Q3",
    start_date=date(2025, 1, 1),
    end_date=date(2025, 9, 30),
    save=True
)
```

---

## Django Management Command (Optional)

You can create a management command to bulk-generate periods:

```bash
python manage.py generate_periods <org_id> <year> --types WEEKLY,MONTHLY,QUARTERLY
```

---

## Migration Summary

### What Was Migrated Automatically

All existing `year` and `quarter` periods were automatically converted:

| Old Data       | New Data                                         |
| -------------- | ------------------------------------------------ |
| year=2025, quarter=1 | name="Q1 2025", type=QUARTERLY, start=2025-01-01, end=2025-03-31 |
| year=2025, quarter=2 | name="Q2 2025", type=QUARTERLY, start=2025-04-01, end=2025-06-30 |
| year=2025, quarter=3 | name="Q3 2025", type=QUARTERLY, start=2025-07-01, end=2025-09-30 |
| year=2025, quarter=4 | name="Q4 2025", type=QUARTERLY, start=2025-10-01, end=2025-12-31 |
| year=2025, quarter=None | name="2025", type=ANNUAL, start=2025-01-01, end=2025-12-31 |

### Database Constraints

- **Unique constraint**: `(organization, name)` - prevents duplicate names per org
- **Validation**: `start_date` must be before `end_date`
- **Overlap check**: Periods cannot overlap within the same organization
- **Indexes**: Optimized for queries on `organization + status`, `organization + period_type`, and `start_date + end_date`

---

## Example: Complete Workflow

```python
from submissions.services.period_generation import generate_reporting_periods, generate_custom_period
from organizations.models import Organization
from datetime import date

# 1. Get organization
org = Organization.objects.get(name="Bygates Company")

# 2. Generate standard periods for 2025
generate_reporting_periods(
    organization=org,
    year=2025,
    period_types=["QUARTERLY", "ANNUAL"],
    save=True
)

# 3. Create custom period for special project
generate_custom_period(
    organization=org,
    name="Net Zero Initiative Phase 1",
    start_date=date(2025, 6, 1),
    end_date=date(2026, 5, 31),
    save=True
)

# 4. List all periods
periods = org.reporting_periods.filter(is_active=True).order_by('start_date')
for period in periods:
    print(f"{period.name}: {period.start_date} to {period.end_date}")
```

---

## Postman Collection Update

Update your Postman requests to use the new schema:

**Old Request:**
```json
{
  "year": 2025,
  "quarter": 1
}
```

**New Request:**
```json
{
  "name": "Q1 2025",
  "period_type": "QUARTERLY",
  "start_date": "2025-01-01",
  "end_date": "2025-03-31"
}
```

---

## Frontend Integration

Update your frontend forms to include:

1. **Period Name** input field (text)
2. **Period Type** dropdown (DAILY, WEEKLY, MONTHLY, QUARTERLY, ANNUAL, CUSTOM)
3. **Start Date** date picker
4. **End Date** date picker

Optionally, add helper buttons to:
- Auto-fill dates based on period type
- Generate all periods for a year at once

---

## Benefits of This Refactor

✅ **Flexible reporting frequencies** - Support daily, weekly, monthly, quarterly, and custom periods  
✅ **Better data granularity** - Track environmental data at appropriate intervals  
✅ **Compliance ready** - Meet various regulatory reporting requirements  
✅ **Project-based tracking** - Custom periods for specific initiatives  
✅ **Automated generation** - Bulk-create periods for entire years  
✅ **Backward compatible** - Existing data automatically migrated  
✅ **Database optimized** - Proper indexes and constraints for performance  

---

## Support

For issues or questions, contact the development team.
