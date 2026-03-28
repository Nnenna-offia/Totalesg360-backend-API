# Reporting Period Auto-Generation API

## Overview

The ReportingPeriod creation has been refactored to **automatically generate** periods instead of requiring manual creation. You now provide a `year` and `period_type`, and the system generates all appropriate periods for that year.

---

## API Endpoint

**POST** `/api/v1/submissions/periods/`

### Headers
```
X-ORG-ID: <organization-uuid>
X-CSRFToken: <csrf-token>
Content-Type: application/json
```

### Request Payload

```json
{
  "year": 2025,
  "period_type": "QUARTERLY"
}
```

### Supported Period Types

- `DAILY` - Generates 365 daily periods
- `WEEKLY` - Generates ~52 weekly periods
- `BI_WEEKLY` - Generates ~26 bi-weekly periods
- `MONTHLY` - Generates 12 monthly periods
- `QUARTERLY` - Generates 4 quarterly periods (Q1, Q2, Q3, Q4)
- `SEMI_ANNUAL` - Generates 2 semi-annual periods (H1, H2)
- `ANNUAL` - Generates 1 annual period

---

## Examples

### Example 1: Generate Quarterly Periods

**Request:**
```json
{
  "year": 2025,
  "period_type": "QUARTERLY"
}
```

**Success Response (201 Created):**
```json
{
  "success": true,
  "data": [
    {
      "id": "uuid-1",
      "organization": "org-uuid",
      "name": "Q1 2025",
      "period_type": "QUARTERLY",
      "start_date": "2025-01-01",
      "end_date": "2025-03-31",
      "status": "OPEN",
      "opened_at": "2026-03-28T12:00:00Z",
      "locked_at": null,
      "is_active": true
    },
    {
      "id": "uuid-2",
      "organization": "org-uuid",
      "name": "Q2 2025",
      "period_type": "QUARTERLY",
      "start_date": "2025-04-01",
      "end_date": "2025-06-30",
      "status": "OPEN",
      "opened_at": "2026-03-28T12:00:00Z",
      "locked_at": null,
      "is_active": true
    },
    {
      "id": "uuid-3",
      "organization": "org-uuid",
      "name": "Q3 2025",
      "period_type": "QUARTERLY",
      "start_date": "2025-07-01",
      "end_date": "2025-09-30",
      "status": "OPEN",
      "opened_at": "2026-03-28T12:00:00Z",
      "locked_at": null,
      "is_active": true
    },
    {
      "id": "uuid-4",
      "organization": "org-uuid",
      "name": "Q4 2025",
      "period_type": "QUARTERLY",
      "start_date": "2025-10-01",
      "end_date": "2025-12-31",
      "status": "OPEN",
      "opened_at": "2026-03-28T12:00:00Z",
      "locked_at": null,
      "is_active": true
    }
  ],
  "meta": {
    "message": "Successfully generated 4 QUARTERLY periods for 2025",
    "count": 4,
    "created": true
  }
}
```

---

### Example 2: Generate Monthly Periods

**Request:**
```json
{
  "year": 2026,
  "period_type": "MONTHLY"
}
```

**Success Response (201 Created):**
```json
{
  "success": true,
  "data": [
    {
      "id": "uuid",
      "name": "Jan 2026",
      "period_type": "MONTHLY",
      "start_date": "2026-01-01",
      "end_date": "2026-01-31",
      "status": "OPEN",
      ...
    },
    {
      "id": "uuid",
      "name": "Feb 2026",
      "period_type": "MONTHLY",
      "start_date": "2026-02-01",
      "end_date": "2026-02-28",
      "status": "OPEN",
      ...
    },
    ... // 10 more months
  ],
  "meta": {
    "message": "Successfully generated 12 MONTHLY periods for 2026",
    "count": 12,
    "created": true
  }
}
```

---

### Example 3: Duplicate Detection

If you try to generate periods that already exist:

**Request:**
```json
{
  "year": 2025,
  "period_type": "QUARTERLY"
}
```

**Response (200 OK - No new creation):**
```json
{
  "success": true,
  "data": [
    ... // existing Q1-Q4 2025 periods
  ],
  "meta": {
    "message": "QUARTERLY periods for 2025 already exist",
    "count": 4,
    "created": false
  }
}
```

Notice `created: false` indicates existing periods were returned.

---

### Example 4: Annual Period

**Request:**
```json
{
  "year": 2027,
  "period_type": "ANNUAL"
}
```

**Success Response (201 Created):**
```json
{
  "success": true,
  "data": [
    {
      "id": "uuid",
      "name": "2027",
      "period_type": "ANNUAL",
      "start_date": "2027-01-01",
      "end_date": "2027-12-31",
      "status": "OPEN",
      ...
    }
  ],
  "meta": {
    "message": "Successfully generated 1 ANNUAL periods for 2027",
    "count": 1,
    "created": true
  }
}
```

---

## Error Responses

### Invalid Year (400 Bad Request)

**Request:**
```json
{
  "year": 1999,
  "period_type": "QUARTERLY"
}
```

**Response:**
```json
{
  "type": "https://dev-backend.totalesg360.com/problems/validation-error",
  "title": "Validation Error",
  "status": 400,
  "detail": {
    "year": ["Year must be 2016 or later"]
  }
}
```

---

### Invalid Period Type (400 Bad Request)

**Request:**
```json
{
  "year": 2025,
  "period_type": "INVALID"
}
```

**Response:**
```json
{
  "type": "https://dev-backend.totalesg360.com/problems/validation-error",
  "title": "Validation Error",
  "status": 400,
  "detail": {
    "period_type": ["\"INVALID\" is not a valid choice."]
  }
}
```

---

### Missing Required Fields (400 Bad Request)

**Request:**
```json
{
  "year": 2025
}
```

**Response:**
```json
{
  "type": "https://dev-backend.totalesg360.com/problems/validation-error",
  "title": "Validation Error",
  "status": 400,
  "detail": {
    "period_type": ["This field is required."]
  }
}
```

---

## Date Ranges Reference

### Quarterly Periods
| Quarter | Start Date | End Date   |
|---------|------------|------------|
| Q1      | Jan 1      | Mar 31     |
| Q2      | Apr 1      | Jun 30     |
| Q3      | Jul 1      | Sep 30     |
| Q4      | Oct 1      | Dec 31     |

### Semi-Annual Periods
| Period | Start Date | End Date   |
|--------|------------|------------|
| H1     | Jan 1      | Jun 30     |
| H2     | Jul 1      | Dec 31     |

### Monthly Periods
Generated for all 12 months with appropriate end dates (28/29/30/31 days).

### Weekly Periods
Generated starting from January 1st, creating ~52 weeks per year.

---

## Postman Collection Update

### Old Payload (Manual Creation)
```json
{
  "name": "Q1 2025",
  "period_type": "QUARTERLY",
  "start_date": "2025-01-01",
  "end_date": "2025-03-31"
}
```

### New Payload (Auto-Generation)
```json
{
  "year": 2025,
  "period_type": "QUARTERLY"
}
```

**Result:** Automatically creates Q1, Q2, Q3, Q4 with correct dates.

---

## Python Usage

If you need to generate periods programmatically:

```python
from submissions.services.period_generation import generate_reporting_periods
from organizations.models import Organization

org = Organization.objects.get(name="Your Company")

# Generate quarterly periods for 2025
results = generate_reporting_periods(
    organization=org,
    year=2025,
    period_types=["QUARTERLY"],
    save=True
)

# Results: 4 periods created (Q1-Q4)
print(f"Created {len(results['QUARTERLY'])} periods")
```

---

## Features

✅ **Automatic Generation** - No manual date entry required  
✅ **Duplicate Prevention** - Returns existing periods if already created  
✅ **Bulk Creation** - Creates all periods for a year at once  
✅ **Consistent Naming** - Standardized names (Q1 2025, Jan 2026, etc.)  
✅ **Date Validation** - Ensures correct quarter/month boundaries  
✅ **No Overlaps** - Periods are sequential with no gaps or overlaps  

---

## Migration Path

### Before (Manual Creation)
Users had to manually create each period with specific dates:
- POST with name, start_date, end_date for each period
- Error-prone (wrong dates, overlaps, typos)
- Time-consuming for multiple periods

### After (Auto-Generation)
Users specify year and type, system generates all periods:
- Single POST creates all periods for the year
- Guaranteed correct dates
- Consistent naming
- Duplicate detection built-in

---

## Best Practices

1. **Generate at Year Start**: Create periods at the beginning of the year
2. **One Period Type per Year**: Generate QUARTERLY for strategic planning, MONTHLY for operations
3. **Check for Duplicates**: API returns existing periods if already created
4. **Lock When Complete**: Lock periods after data submission is complete

---

## Common Use Cases

### Setup New Organization
```json
// Generate quarterly periods for current year
{"year": 2026, "period_type": "QUARTERLY"}

// Generate monthly periods for detailed tracking
{"year": 2026, "period_type": "MONTHLY"}
```

### Multi-Year Planning
```json
// Generate 2025 periods
{"year": 2025, "period_type": "QUARTERLY"}

// Generate 2026 periods
{"year": 2026, "period_type": "QUARTERLY"}

// Generate 2027 periods
{"year": 2027, "period_type": "QUARTERLY"}
```

### Different Frequencies
```json
// Weekly for operational tracking
{"year": 2026, "period_type": "WEEKLY"}

// Quarterly for executive reporting
{"year": 2026, "period_type": "QUARTERLY"}

// Annual for regulatory compliance
{"year": 2026, "period_type": "ANNUAL"}
```

---

## Support

For questions or issues, contact the development team.
