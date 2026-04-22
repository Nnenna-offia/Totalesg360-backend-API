# Organization ESG Onboarding API

This document explains the full backend flow from first-time onboarding to ESG configuration and first data submission.

It focuses on what the frontend needs to send, what the backend creates automatically, and what must not be sent manually.

## Overview

From onboarding alone, the system now does all of the following automatically:

- Creates the first organization as a `group`
- Assigns regulatory frameworks based on sector and primary reporting focus
- Creates default `OrganizationESGSettings` for that organization
- Creates or resolves the active reporting period from ESG settings
- Uses the active reporting period automatically for submissions
- Filters indicators based on enabled ESG modules

The frontend must not send `reporting_period_id` when submitting indicators or activities.

## Base URLs

- Signup: `POST /api/v1/auth/signup/`
- OTP request: `POST /api/v1/auth/request-otp/`
- OTP verify: `POST /api/v1/auth/verify-otp/`
- Login: `POST /api/v1/auth/login/`
- ESG settings: `GET/PATCH /api/v1/organizations/esg-settings/`
- ESG settings by org id: `GET/PATCH /api/v1/organizations/{organization_id}/esg-settings/`
- Framework selection: `GET/PATCH /api/v1/organizations/frameworks/`
- Submit indicator: `POST /api/v1/submissions/submit/`
- Submit activity: `POST /api/v1/activities/submissions/`
- Bulk activity submit: `POST /api/v1/activities/submissions/bulk/create/`

## Step 1: Signup

Create the user and the root organization in one call.

Endpoint:

```http
POST /api/v1/auth/signup/
Content-Type: application/json
```

Payload:

```json
{
  "email": "admin@tgi.com",
  "password": "StrongPassword123",
  "first_name": "TGI",
  "last_name": "Admin",
  "organization_name": "TGI Group",
  "sector": "manufacturing",
  "country": "NG",
  "primary_reporting_focus": "HYBRID"
}
```

What the backend does:

- Creates the user
- Creates the organization as entity type `group`
- Creates memberships and base organization data
- Bootstraps regulatory frameworks from `sector` + `primary_reporting_focus`
- Creates default ESG settings for the organization
- Creates an active reporting period from the default ESG settings
- Sends or queues OTP verification

Typical success response:

```json
{
  "success": true,
  "data": {
    "user_id": "0b3d2f86-8c91-4a3a-8d24-bfbb71d6f5c2",
    "email": "admin@tgi.com",
    "organization_id": "1c20c0c7-3810-4e0f-9072-2303c88ff220",
    "organization_name": "TGI Group",
    "sector": "manufacturing",
    "primary_reporting_focus": "HYBRID",
    "verification_required": true,
    "otp_sent": true
  }
}
```

Important:

- The returned `organization_id` is the organization context the frontend will use later.
- Frameworks are part of onboarding setup, but they are not manually selected in the signup payload today.
- Framework assignment is currently automatic.

## Framework Setup Behavior

Framework setup is tied to onboarding, but not through a separate `framework_ids` or `framework_select` field.

Current backend behavior:

- During signup, frameworks are assigned automatically from `sector`
- During signup, frameworks are also assigned from `primary_reporting_focus`
- Nigerian focus assigns active Nigerian frameworks that are cross-sector or match the selected sector
- International focus assigns active international cross-sector frameworks
- Hybrid focus assigns both Nigerian and international frameworks

This means the current implementation is:

- tied to setup: yes
- user-selected during setup: no
- tied to ESG settings update: no

So there are two separate concerns:

- framework assignment: bootstrapped during signup
- ESG settings: used for module enablement, reporting level, and reporting frequency

If the product requirement is that the user explicitly selects frameworks during onboarding, that is not implemented in the current API contract yet.

After onboarding, the frontend can now let users activate or deactivate preloaded frameworks through the dedicated framework selection endpoint.

## Reading Assigned Frameworks

The main organization settings payload includes frameworks alongside ESG settings.

Endpoint:

```http
GET /api/v1/organizations/settings/
X-ORG-ID: 1c20c0c7-3810-4e0f-9072-2303c88ff220
```

The response includes:

- `organization`
- `settings`
- `esg_settings`
- `frameworks`
- `departments`

`frameworks` now reflects organization framework assignments as the source of truth, including active and inactive assignment rows.

## Step 5A: Read Available Frameworks

Use the framework selection endpoint to render UI checkboxes from system-managed frameworks.

```http
GET /api/v1/organizations/frameworks/
X-ORG-ID: 1c20c0c7-3810-4e0f-9072-2303c88ff220
```

Typical response:

```json
{
  "success": true,
  "data": {
    "frameworks": [
      {
        "assignment_id": "8df9205a-d0db-49b7-9a6a-03774d569792",
        "framework_id": "15d228c2-bad1-40b5-87bc-e83a23ad4cf5",
        "code": "GRI",
        "name": "Global Reporting Initiative (GRI Standards)",
        "jurisdiction": "INTERNATIONAL",
        "description": "World's most widely used sustainability reporting standards",
        "sector": "",
        "priority": 100,
        "framework_is_active": true,
        "is_system": true,
        "is_assigned": true,
        "is_active": true,
        "is_enabled": true,
        "is_primary": true,
        "assigned_at": "2026-04-21T08:10:00Z"
      },
      {
        "assignment_id": null,
        "framework_id": "8fed20bb-b2d1-4d0f-ac2d-0f9d9b35f1c2",
        "code": "TCFD",
        "name": "Task Force on Climate-related Financial Disclosures",
        "jurisdiction": "INTERNATIONAL",
        "description": "Framework for climate-related financial risk disclosures",
        "sector": "",
        "priority": 90,
        "framework_is_active": true,
        "is_system": true,
        "is_assigned": false,
        "is_active": false,
        "is_enabled": false,
        "is_primary": false,
        "assigned_at": null
      }
    ]
  }
}
```

UI rule:

- Checkbox checked means `is_active = true`
- Checkbox unchecked means `is_active = false`
- Frameworks are system-preloaded and must not be created or edited by the frontend

## Step 2: Request OTP

If the OTP needs to be resent:

```http
POST /api/v1/auth/request-otp/
Content-Type: application/json
```

Payload:

```json
{
  "email": "admin@tgi.com"
}
```

## Step 3: Verify OTP

Activate the account before login.

```http
POST /api/v1/auth/verify-otp/
Content-Type: application/json
```

Payload:

```json
{
  "email": "admin@tgi.com",
  "otp": "123456"
}
```

## Step 4: Login

Authenticate and receive cookies plus organization memberships.

Endpoint:

```http
POST /api/v1/auth/login/
Content-Type: application/json
```

Payload:

```json
{
  "email": "admin@tgi.com",
  "password": "StrongPassword123"
}
```

Typical response body:

```json
{
  "user": {
    "id": "0b3d2f86-8c91-4a3a-8d24-bfbb71d6f5c2",
    "email": "admin@tgi.com",
    "first_name": "TGI",
    "last_name": "Admin"
  },
  "memberships": [
    {
      "organization_id": "1c20c0c7-3810-4e0f-9072-2303c88ff220",
      "organization_name": "TGI Group"
    }
  ],
  "csrf_token": "masked-csrf-token"
}
```

Frontend requirements after login:

- Keep the auth cookies set by the backend
- Send `X-CSRFToken` with write requests
- Send `X-ORG-ID: {organization_id}` on organization-scoped requests unless using the path-based ESG settings endpoint

Example headers for authenticated write calls:

```http
X-ORG-ID: 1c20c0c7-3810-4e0f-9072-2303c88ff220
X-CSRFToken: masked-csrf-token
Content-Type: application/json
```

## Step 5: Read ESG Settings

The organization already has ESG settings immediately after signup.

Header-based endpoint:

```http
GET /api/v1/organizations/esg-settings/
X-ORG-ID: 1c20c0c7-3810-4e0f-9072-2303c88ff220
```

Path-based endpoint:

```http
GET /api/v1/organizations/1c20c0c7-3810-4e0f-9072-2303c88ff220/esg-settings/
```

Typical response:

```json
{
  "success": true,
  "data": {
    "enable_environmental": true,
    "enable_social": true,
    "enable_governance": true,
    "reporting_level": "group",
    "reporting_frequency": "MONTHLY",
    "fiscal_year_start_month": 1,
    "sector_defaults": {},
    "updated_at": "2026-04-21T07:30:00Z"
  }
}
```

Default values after onboarding:

- `reporting_level` defaults to the organization entity type
- First organization created from signup becomes `group`
- `reporting_frequency` defaults to `MONTHLY`
- All three ESG modules are enabled by default

## Step 6A: Update Framework Selection

Use this after onboarding if the organization wants to opt frameworks in or out.

```http
PATCH /api/v1/organizations/frameworks/
X-ORG-ID: 1c20c0c7-3810-4e0f-9072-2303c88ff220
X-CSRFToken: masked-csrf-token
Content-Type: application/json
```

Payload:

```json
{
  "frameworks": [
    {
      "framework_id": "15d228c2-bad1-40b5-87bc-e83a23ad4cf5",
      "is_active": true
    },
    {
      "framework_id": "8fed20bb-b2d1-4d0f-ac2d-0f9d9b35f1c2",
      "is_active": false
    }
  ]
}
```

Backend behavior:

- Only system-managed frameworks can be selected
- Existing assignments are updated in place
- Missing assignment rows are created automatically when a framework is toggled
- Active frameworks are normalized so one active framework remains primary when possible
- Indicator activation updates dynamically from active frameworks plus ESG module settings

## Step 6: Update ESG Settings

This controls reporting behavior for the organization.

Endpoint:

```http
PATCH /api/v1/organizations/esg-settings/
X-ORG-ID: 1c20c0c7-3810-4e0f-9072-2303c88ff220
X-CSRFToken: masked-csrf-token
Content-Type: application/json
```

Payload example:

```json
{
  "enable_environmental": true,
  "enable_social": true,
  "enable_governance": false,
  "reporting_level": "facility",
  "reporting_frequency": "MONTHLY",
  "fiscal_year_start_month": 10
}
```

Validation rules:

- At least one of `enable_environmental`, `enable_social`, or `enable_governance` must be `true`
- `reporting_frequency` must match the existing `ReportingPeriod.PeriodType` enum values
- `fiscal_year_start_month` must be between `1` and `12`

What the backend does on successful update:

- Saves the ESG settings
- Ensures there is exactly one active reporting period for the organization and selected frequency
- Deactivates any previous active period for the same frequency when needed

Typical response:

```json
{
  "success": true,
  "data": {
    "enable_environmental": true,
    "enable_social": true,
    "enable_governance": false,
    "reporting_level": "facility",
    "reporting_frequency": "MONTHLY",
    "fiscal_year_start_month": 10,
    "sector_defaults": {},
    "updated_at": "2026-04-21T08:00:00Z"
  },
  "meta": {
    "message": "ESG settings updated successfully"
  }
}
```

## Auto-Managed Reporting Periods

The backend manages reporting periods automatically from ESG settings.

Frontend must not:

- Create a reporting period before every submission
- Ask users to manually choose a reporting period for standard submissions
- Send `reporting_period_id` in indicator submission payloads
- Send `reporting_period_id` in activity submission payloads

Backend behavior:

- Resolves the active period from `organization.esg_settings.reporting_frequency`
- Creates one if none exists
- Attaches that active period to the submission automatically

## Step 7: Submit an Indicator Value

Endpoint:

```http
POST /api/v1/submissions/submit/
X-ORG-ID: 1c20c0c7-3810-4e0f-9072-2303c88ff220
X-CSRFToken: masked-csrf-token
Content-Type: application/json
```

Payload:

```json
{
  "indicator_id": "f0718cbf-bc36-4c99-b936-1cd393e9adf0",
  "value": 120.5,
  "metadata": {
    "source": "finance-team"
  }
}
```

Optional field:

- `facility_id`

Do not send:

```json
{
  "reporting_period_id": "..."
}
```

What the backend does:

- Validates the indicator is active for the organization
- Applies ESG module filtering
- Resolves the active reporting period automatically
- Creates or updates the `DataSubmission`

## Step 8: Submit an Activity Value

Endpoint:

```http
POST /api/v1/activities/submissions/
X-ORG-ID: 1c20c0c7-3810-4e0f-9072-2303c88ff220
X-CSRFToken: masked-csrf-token
Content-Type: application/json
```

Payload:

```json
{
  "activity_type_id": "6f091f25-37a1-4e7d-85d9-e97d60139a3c",
  "value": 3500.000000,
  "facility_id": "1c4c08b8-ef6a-45e5-a447-ecdf040f3d16"
}
```

Bulk payload:

```json
{
  "submissions": [
    {
      "activity_type_id": "6f091f25-37a1-4e7d-85d9-e97d60139a3c",
      "value": 3500.000000,
      "facility_id": "1c4c08b8-ef6a-45e5-a447-ecdf040f3d16"
    },
    {
      "activity_type_id": "f78b1d80-bcb9-48c3-b1d4-510557398dc4",
      "value": 125.000000
    }
  ]
}
```

Do not send `reporting_period_id` in either payload.

What the backend does:

- Resolves the active reporting period automatically
- Creates the activity submission
- Triggers emission calculation and indicator aggregation as best effort

## How ESG Settings Affect Behavior

### Indicator activation

Indicators are filtered by framework assignments and ESG module settings.

Examples:

- If `enable_governance` is `false`, `GOV` indicators are excluded
- If `enable_social` is `false`, `SOC` indicators are excluded
- If `enable_environmental` is `false`, `ENV` indicators are excluded

### Reporting level

`reporting_level` controls which entities are considered reporting entities.

Supported values:

- `group`
- `subsidiary`
- `facility`
- `department`

Examples:

- `group`: report at the root organization itself
- `subsidiary`: report across direct subsidiary children
- `facility`: report across facility entities below the organization tree
- `department`: report across department entities in the hierarchy

### Reporting frequency

`reporting_frequency` controls the active reporting period used by submissions.

Supported backend values:

- `DAILY`
- `WEEKLY`
- `BI_WEEKLY`
- `MONTHLY`
- `QUARTERLY`
- `SEMI_ANNUAL`
- `ANNUAL`
- `CUSTOM`

## Frontend Integration Rules

Required:

- Use signup to create the first organization
- Store `organization_id` from signup or login memberships
- Use `X-ORG-ID` for organization-scoped endpoints
- Use the returned CSRF token for authenticated write calls
- Read and update ESG settings through the dedicated ESG settings endpoint

Do not do this:

- Do not send `reporting_period_id` from onboarding screens or submission forms
- Do not store ESG settings in a frontend-only blob and assume backend behavior matches
- Do not assume all indicators are active when modules are disabled

## Minimal Frontend Flow

1. `POST /api/v1/auth/signup/`
2. `POST /api/v1/auth/verify-otp/`
3. `POST /api/v1/auth/login/`
4. `GET /api/v1/organizations/esg-settings/`
5. `PATCH /api/v1/organizations/esg-settings/`
6. `POST /api/v1/submissions/submit/` or `POST /api/v1/activities/submissions/`

## Example End-to-End Sequence

### 1. Signup

```json
{
  "email": "admin@tgi.com",
  "password": "StrongPassword123",
  "first_name": "TGI",
  "last_name": "Admin",
  "organization_name": "TGI Group",
  "sector": "manufacturing",
  "country": "NG",
  "primary_reporting_focus": "HYBRID"
}
```

### 2. Update ESG settings after first login

```json
{
  "enable_environmental": true,
  "enable_social": true,
  "enable_governance": true,
  "reporting_level": "group",
  "reporting_frequency": "QUARTERLY",
  "fiscal_year_start_month": 1
}
```

### 3. Submit indicator value

```json
{
  "indicator_id": "f0718cbf-bc36-4c99-b936-1cd393e9adf0",
  "value": 120.5
}
```

### 4. Submit activity value

```json
{
  "activity_type_id": "6f091f25-37a1-4e7d-85d9-e97d60139a3c",
  "value": 3500.000000,
  "facility_id": "1c4c08b8-ef6a-45e5-a447-ecdf040f3d16"
}
```

In both submission cases, the reporting period is resolved automatically by the backend.