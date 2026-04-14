# Totalesg360 Backend API - Complete Implementation Guide

**Last Updated**: April 12, 2026  
**Version**: 1.0  
**Project**: ESG Reporting Platform

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture & Design Patterns](#architecture--design-patterns)
3. [Core Authentication System](#core-authentication-system)
4. [Organization & Roles Management](#organization--roles-management)
5. [Indicators & Data Collection](#indicators--data-collection)
6. [Targets & Goal Tracking](#targets--goal-tracking)
7. [Submissions & Reporting](#submissions--reporting)
8. [Compliance Framework](#compliance-framework)
9. [Dashboard & Analytics](#dashboard--analytics)
10. [Activities & Emissions](#activities--emissions)
11. [Configuration & Settings](#configuration--settings)
12. [Error Handling & Responses](#error-handling--responses)
13. [Security & CSRF Protection](#security--csrf-protection)
14. [API Endpoints Reference](#api-endpoints-reference)
15. [Database Schema](#database-schema)

---

## Overview

**Totalesg360** is an Enterprise ESG (Environmental, Social, Governance) reporting and compliance platform built with Django REST Framework. It enables organizations to:

- Track ESG indicators and KPIs
- Set and monitor targets against baselines
- Submit sustainability data across multiple reporting periods
- Manage compliance with regulatory frameworks (Nigeria ESG Code, ISSB, TCFD, etc.)
- Generate comprehensive ESG reports and dashboards
- Support multi-year, multi-frequency reporting scenarios

### Key Features

✅ **Multi-tenant Architecture** - Isolated data per organization  
✅ **JWT + CSRF Authentication** - Secure cookie-based auth for single-page apps  
✅ **Role-Based Access Control** - Fine-grained capabilities per role  
✅ **Dynamic Reporting Frequencies** - Daily, Weekly, Monthly, Quarterly, Annual, etc.  
✅ **Auto-generation of Periods** - Reporting periods auto-created as needed  
✅ **Activity-Based Calculations** - Derive indicators from activities (emissions, fuel usage, etc.)  
✅ **Compliance Tracking** - Track requirements by framework and audit status  
✅ **Real-time Progress** - Instant target progress calculation  
✅ **RFC 7807 Error Responses** - Standardized problem detail format  

---

## Architecture & Design Patterns

### Technology Stack

```
Backend:        Django 6.0+ (Python 3.12)
API Framework:  Django REST Framework (DRF)
Database:       PostgreSQL (via Docker)
Cache/Queue:    Redis + Celery
Authentication: JWT (HttpOnly cookies) + CSRF tokens
Task Scheduler: Celery Beat (database-backed)
```

### Design Patterns Used

#### 1. **HackSoft Architecture Pattern**

The platform uses HackSoft's service-oriented Django architecture:

```
Models (database layer)
    ↓
Selectors (read-only queries with business logic)
    ↓
Services (write operations and side effects)
    ↓
API Views (HTTP interface)
    ↓
Serializers (input validation + transformation)
```

**Benefits:**
- Clear separation of concerns
- Reusable business logic (can call services from tasks, signals, other services)
- Testable components
- No circular dependencies

#### 2. **Layered Package Structure**

Each app follows this structure:

```
src/app_name/
├── models/              # Database models (one per file for large apps)
├── selectors/           # Read-only query logic
├── services/            # Business logic (creates, updates, side effects)
├── api/
│   ├── views.py         # API endpoints
│   ├── serializers.py   # Input validation & response formatting
│   └── urls.py          # URL routing
├── management/          # Custom Django commands
├── migrations/          # Database migrations
└── tests/               # Unit & integration tests
```

#### 3. **Problem Detail Response Format (RFC 7807)**

All errors return structured problem details:

```json
{
  "type": "https://totalesg360.com/probs/validation-error",
  "title": "Validation Error",
  "detail": "Invalid organization ID",
  "code": "invalid_order_number",
  "instance": "/api/v1/orders/",
  "status": 400
}
```

**Benefits:**
- Standardized across all endpoints
- Front-end can parse `code` field for app-specific logic
- URL-based error types allow future documentation
- Compatible with IETF standards

---

## Core Authentication System

### Location
`src/accounts/` app

### Components

#### 1. **Models** (`models/`)

**User Model**
- Extends Django's `AbstractUser`
- Email-based authentication (not username)
- Fields: `email`, `first_name`, `last_name`, `is_active`, `created_at`

**RefreshToken Model**
- Tracks issued refresh tokens
- Fields: `user`, `jti` (JWT ID), `ip_address`, `user_agent`, `created_at`, `is_revoked`
- Purpose: Server-side revocation and session tracking

**EmailVerification Model**
- Tracks OTP codes for email verification
- Fields: `user`, `code`, `created_at`, `expires_at`, `is_verified`

**PasswordReset Model**
- Tracks OTP codes for password resets
- Fields: `user`, `code`, `created_at`, `expires_at`, `is_verified`

#### 2. **Token System** (`auth/tokens.py`)

**JWT Structure**
```python
{
  "user_id": "uuid",
  "jti": "unique-token-id",
  "iat": 1234567890,           # issued at
  "exp": 1234567890 + 300,     # expires in 5 minutes (access) or 7 days (refresh)
  "iss": "totalesg360",        # issuer
}
```

**Token Types:**
- **access_token** (5 min default): Used for API requests
- **refresh_token** (7 days default): Used to get new access_token

**Token Functions:**
```python
make_token(payload, lifetime, jti) -> str
    Create and sign a JWT

decode_token(token) -> dict
    Verify and decode JWT, raise exceptions on invalid
```

#### 3. **Authentication Class** (`auth/authentication.py`)

**CookieJWTAuthentication**
- Implements DRF's `BaseAuthentication`
- Reads `access_token` from HttpOnly cookie
- Validates JWT signature and expiry
- Enforces CSRF protection on non-safe methods (POST, PUT, DELETE)
- Returns `(user, payload)` tuple on success

**CSRF Validation:**
- For authenticated requests with mutations (POST, PUT, DELETE):
  1. Calls Django's `CsrfViewMiddleware`
  2. Validates `X-CSRFToken` header matches `csrftoken` cookie
  3. Raises `PermissionDenied` if mismatch

#### 4. **Services** (`services/auth.py`)

**Core Functions:**

```python
authenticate_user(email: str, password: str) -> User
    Validate credentials, return User or raise Unauthorized

create_access_token(user) -> str
    Create 5-min access token

create_refresh_token(user, ip_address, user_agent) -> (str, str)
    Create 7-day refresh token + jti ID
    Store in RefreshToken model for revocation tracking

rotate_refresh_token(old_jti: str, user) -> (str, str)
    Revoke old token, create new one
    Used on each refresh (security best practice)

revoke_refresh_token(jti: str)
    Mark token as revoked in DB

revoke_all_user_tokens(user)
    Revoke all of user's refresh tokens (logout from all devices)
```

#### 5. **API Views** (`api/views.py`)

**Cookie Configuration Helper**
```python
def get_cookie_config(cookie_type: str) -> dict
    Returns secure settings based on DEBUG:
    - Dev (HTTP):  secure=False, samesite="Lax"
    - Prod (HTTPS): secure=True, samesite="None"
    
    Types: "access", "refresh", "csrf"
```

**Authentication Endpoints:**

| Endpoint | Method | Purpose | Cookies Set |
|----------|--------|---------|------------|
| `/api/v1/auth/login/` | POST | Login with email/password | access, refresh, csrf |
| `/api/v1/auth/logout/` | POST | Logout & revoke tokens | (cleared) |
| `/api/v1/auth/refresh/` | POST | Get new access token | access, refresh, csrf |
| `/api/v1/auth/csrf/` | GET | Bootstrap CSRF token | csrf |
| `/api/v1/auth/signup/` | POST | Create user + org | (no auth) |
| `/api/v1/auth/request-otp/` | POST | Request email OTP | (no auth) |
| `/api/v1/auth/verify-otp/` | POST | Activate user | (no auth) |
| `/api/v1/auth/request-password-reset/` | POST | Request reset OTP | (no auth) |
| `/api/v1/auth/reset-password/` | POST | Reset password | (no auth) |

**LoginView (POST /api/v1/auth/login/)**
- Input: `{email, password}`
- Output: `{user, memberships, csrf_token}` + cookies
- CSRF token rotated on each login (prevents fixation attacks)

**RefreshView (POST /api/v1/auth/refresh/)**
- Input: (none - reads from cookies)
- Output: `{csrf_token}` + new cookies
- CSRF token rotated on refresh (consistency)

**CSRFView (GET /api/v1/auth/csrf/)**
- Input: (none)
- Output: `{csrf_token}`
- Purpose: Bootstrap endpoint for unauthenticated operations
- Used before login for signup/password-reset operations

**SignupView (POST /api/v1/auth/signup/)**
- Creates user + organization + initial membership + role
- Input validation via `SignupSerializer`
- Calls `signup_service()` for business logic
- Returns user ID and organization ID

**OTP Endpoints**
- `RequestOTPView`: Send OTP via email (rate-limited: 6/hour)
- `VerifyOTPView`: Verify code and activate user
- `RequestPasswordResetView`: Send password reset OTP
- `ResetPasswordView`: Verify OTP and set new password

#### 6. **Serializers** (`api/serializers.py`)

```python
LoginSerializer
    email: EmailField
    password: CharField (write-only)

SignupSerializer
    User: email, password, first_name, last_name
    Org: organization_name, sector, country, primary_reporting_focus

RequestOTPSerializer / VerifyOTPSerializer
RequestPasswordResetSerializer / ResetPasswordSerializer
    Various OTP-based operations

ChangePasswordSerializer
    old_password, new_password (for authenticated users)
```

#### 7. **Settings Configuration** (`config/settings/base.py`)

**JWT Configuration**
```python
JWT_SECRET = os.getenv("JWT_SECRET", SECRET_KEY)
JWT_ALGORITHM = "HS256"
JWT_ISS = "totalesg360"
JWT_ACCESS_LIFETIME_SECONDS = 300      # 5 minutes
JWT_REFRESH_LIFETIME_SECONDS = 604800  # 7 days
```

**Cookie Configuration** (Dynamic based on DEBUG)
```python
# Development (HTTP/localhost):
CSRF_COOKIE_SECURE = False
CSRF_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_SECURE = False
SESSION_COOKIE_SAMESITE = "Lax"

# Production (HTTPS):
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_SAMESITE = "None"
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_SAMESITE = "None"
```

**OTP Configuration**
```python
OTP_TTL_SECONDS = 3600          # 1 hour
OTP_LENGTH = 6                   # characters
OTP_MAX_REQUESTS_PER_HOUR = 6   # rate limit
OTP_MAX_RESEND_PER_HOUR = 5
```

### Frontend Integration

**CSRF Flow:**
```javascript
// 1. Login
const res = await fetch('/api/v1/auth/login/', {
  method: 'POST',
  credentials: 'include',  // ← REQUIRED for cookies
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({email, password})
});
const {csrf_token} = await res.json();
localStorage.setItem('csrf_token', csrf_token);

// 2. Make mutation (POST/PUT/DELETE)
await fetch('/api/v1/indicators/', {
  method: 'POST',
  credentials: 'include',  // ← Browser sends cookies
  headers: {
    'X-CSRFToken': localStorage.getItem('csrf_token')  // ← Send your token
  }
});

// 3. Token refresh (when access_token expires)
const refreshRes = await fetch('/api/v1/auth/refresh/', {
  method: 'POST',
  credentials: 'include'
});
const {csrf_token: newToken} = await refreshRes.json();
localStorage.setItem('csrf_token', newToken);  // ← Update
```

See [docs/CSRF_STRATEGY.md](docs/CSRF_STRATEGY.md) for complete frontend examples.

---

## Organization & Roles Management

### Location
`src/organizations/` app  
`src/roles/` app

### Components

#### 1. **Organization Models** (`models/organization.py`)

**Organization Model**
```python
Fields:
- name: CharField (max 255)
- registration_number: CharField (max 100)
- registered_name: CharField (max 500)
- website: URLField
- sector: CharField (choices: manufacturing, oil_gas, finance, etc.)
- country: CharField (ISO 3166-1 alpha-2)
- company_size: CharField (choices: small, medium, large, enterprise)
- primary_reporting_focus: CharField (choices: NIGERIA, INTERNATIONAL, HYBRID)
- logo: ImageField (optional, uploads to organization_logos/)
- description: TextField
- is_active: BooleanField
- created_at: DateTimeField
- updated_at: DateTimeField

Relations:
- memberships: M2M via Membership
- departments: 1-N via Department
- settings: 1-1 via OrganizationSettings
```

**Department Model**
```python
Fields:
- organization: ForeignKey (Organization)
- name: CharField (max 255)
- code: CharField (max 50)
- description: TextField (optional)
- is_active: BooleanField

Uniqueness:
- (organization, name) together must be unique
```

**OrganizationSettings Model**
```python
OneToOne with Organization (related_name='system_settings')

General Settings:
- system_language: CharField (default: en-US)
- timezone: CharField (default: UTC)
- currency: CharField (default: USD)
- date_format: CharField (default: YYYY-MM-DD)
- admin_theme: CharField (default: light)
- notifications_enabled: BooleanField (default: True)
- system_update_frequency: CharField (choices: daily, weekly, monthly)
- export_formats: JSONField (choices: PDF, Excel, CSV, JSON)

Security Settings:
- security_checks_frequency: CharField (choices: daily, weekly, monthly)
- require_2fa: BooleanField (default: False)
- encrypt_stored_data: BooleanField (default: False)
- encryption_method: CharField (choices: AES-256, RSA-2048)
```

#### 2. **Membership & Role Models** (`models/membership.py`, `roles/models/`)

**Membership Model**
```python
Fields:
- organization: ForeignKey (Organization)
- user: ForeignKey (User)
- role: ForeignKey (Role)
- is_active: BooleanField
- created_at: DateTimeField

Purpose:
- Connects users to organizations with a specific role
- One user can have multiple memberships across orgs
```

**Role Model** (`roles/models/role.py`)
```python
Fields:
- organization: ForeignKey (Organization, nullable for system roles)
- name: CharField
- code: CharField (e.g., "admin", "reporter", "viewer")
- description: TextField
- capabilities: M2M via RoleCapability
- is_active: BooleanField
- is_system_role: BooleanField (for pre-defined roles)

Capabilities Examples:
- organization.manage_settings
- indicators.create
- submissions.view
- reports.export
- complians.manage
```

**Capability Model** (`roles/models/capability.py`)
```python
Fields:
- code: CharField (unique, e.g., "indicators.create")
- name: CharField
- category: CharField (organization, indicators, submissions, etc.)
- description: TextField
```

#### 3. **Selectors** (`selectors/`)

**Organization Selectors:**
```python
get_organization_settings(organization_id)
    Returns settings with departments and frameworks

get_organization_with_settings(organization_id)
    Returns org with settings, auto-creates if missing

get_user_memberships_with_roles(user)
    Returns all user's memberships with role capabilities
```

**Role Selectors:**
```python
get_user_capabilities(user, organization)
    Returns all capabilities for user in org

has_capability(user, organization, capability_code)
    Boolean check
```

#### 4. **Services** (`services/`)

**Organization Services:**
```python
update_general_settings(organization, **kwargs)
    Validates and updates general settings
    Raises ValidationError for invalid values

update_security_settings(organization, **kwargs)
    Validates and updates security settings
    Transaction-wrapped
```

#### 5. **API Views & Serializers**

**Organization APIs:**

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v1/organizations/` | GET/POST | List/Create organizations |
| `/api/v1/organizations/{id}/` | GET/PATCH/DELETE | Organization CRUD |
| `/api/v1/organizations/{id}/settings/` | GET | Get all settings |
| `/api/v1/organizations/{id}/settings/general/` | PATCH | Update general settings |
| `/api/v1/organizations/{id}/settings/security/` | PATCH | Update security settings |
| `/api/v1/organizations/options/` | GET | Metadata (sectors, focus types) |

**OrganizationSettingsView (GET /api/v1/organizations/{id}/settings/)**
```json
Response:
{
  "organization": {...details...},
  "settings": {...all settings...},
  "departments": [...],
  "frameworks": [...assigned frameworks...]
}
```

**GeneralSettingsUpdateView (PATCH /api/v1/organizations/{id}/settings/general/)**
```json
Request:
{
  "system_language": "en-US",
  "timezone": "Africa/Lagos",
  "currency": "NGN"
}
```

**SecuritySettingsUpdateView (PATCH /api/v1/organizations/{id}/settings/security/)**
```json
Request:
{
  "require_2fa": true,
  "security_checks_frequency": "weekly"
}
```

---

## Indicators & Data Collection

### Location
`src/indicators/` app

### Components

#### 1. **Indicator Models** (`models/indicator.py`)

**Indicator Model**
```python
Fields:
- organization: ForeignKey (Organization)
- code: CharField (e.g., GHG001, WASTE-H2O, SOC-001)
- name: CharField
- description: TextField
- unit: CharField (tonnes, MWh, litres, etc.)
- collection_method: CharField (choices: DIRECT, ACTIVITY)
  - DIRECT: User submits values directly
  - ACTIVITY: Calculated from activities (e.g., GHG from fuel)
- category: CharField (choices: EMISSIONS, WATER, WASTE, SOCIAL, GOVERNANCE)
- is_active: BooleanField
- created_at: DateTimeField

Relations:
- organization: FK
- activity_types: M2M (if collection_method=ACTIVITY)
- targets: 1-N via TargetGoal
- values: 1-N via IndicatorValue
```

**IndicatorValue Model** (Calculated view of indicator data)
```python
Fields:
- organization: ForeignKey
- indicator: ForeignKey
- reporting_period: ForeignKey
- facility: ForeignKey (optional)
- value: FloatField (aggregated from submissions)
- metadata: JSONField (activity_count, submission_count, etc.)
- calculated_at: DateTimeField

Purpose:
- Cache indicator values for reporting/dashboard
- Auto-updated when submissions are created/updated
- Used by targets and compliance for progress calculation
```

#### 2. **Data Flow: Direct Indicators**

**Flow from Submission to IndicatorValue:**

```
User submits data
    ↓
POST /api/v1/submissions/submit/
{
  "indicator_id": "ind-uuid",
  "reporting_period_id": "period-uuid",
  "value": 100.5
}
    ↓
DataSubmission created
    ↓
submit_data() service called
    ↓
update_indicator_value() triggered via signal
    ↓
IndicatorValue updated
- Aggregates all submissions for period
- Stores in cache for performance
    ↓
Targets can now read from IndicatorValue
    ↓
Progress calculations use latest value
```

#### 3. **Data Flow: Activity-Based Indicators**

**Flow from Activity to Indicator:**

```
User submits activity
    ↓
POST /api/v1/activities/submissions/
{
  "activity_type_id": "act-uuid",
  "reporting_period_id": "period-uuid",
  "value": 50.0,  # e.g., litres of diesel
  "unit": "litres"
}
    ↓
ActivitySubmission created
    ↓
submit_activity_value() service called
    ↓
Emissions calculation triggered (if applicable)
    ↓
update_indicator_value() called for linked indicator
    ↓
IndicatorValue updated with calculated value
- Value = Activity Value × Emission Factor
- Example: 50L diesel × 2.68 kg CO2/L = 134 kg CO2
```

#### 4. **Selectors** (`selectors/`)

```python
get_indicator_values(
    organization,
    reporting_period,
    indicator=None,
    facility=None
)
    Returns all indicator values for period

get_indicator_current_value(indicator, facility=None)
    Returns latest value across all periods

get_indicator_target_progress(target_goal)
    Calculates progress based on indicator values
```

#### 5. **Services** (`services/`)

```python
update_indicator_value(
    organization,
    indicator,
    reporting_period,
    facility=None
)
    Aggregates all submissions for indicator
    Updates or creates IndicatorValue
    Called by signal when submissions are created/updated

calculate_activity_emissions(activity_type, value)
    Uses emission factors to calculate GHG
    Returns CO2e value
```

#### 6. **API Views**

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v1/indicators/` | GET | List indicators |
| `/api/v1/indicators/{id}/` | GET | Indicator detail |
| `/api/v1/indicators/{id}/values/` | GET | Historical values |
| `/api/v1/indicators/batch-values/` | GET | Multiple period values |

---

## Targets & Goal Tracking

### Location
`src/targets/` app

### Components

#### 1. **TargetGoal Model** (`models/target_goal.py`)

**TargetGoal Fields**
```python
Fields:
- organization: ForeignKey (Organization)
- indicator: ForeignKey (Indicator)
- name: CharField
- description: TextField
- department: ForeignKey (Department, optional)
- facility: ForeignKey (Facility, optional)

Reporting Configuration:
- reporting_frequency: CharField (choices: DAILY, WEEKLY, BI_WEEKLY, MONTHLY, QUARTERLY, SEMI_ANNUAL, ANNUAL)
- baseline_year: IntegerField
- baseline_value: FloatField
- target_year: IntegerField
- target_value: FloatField
- direction: CharField (choices: INCREASE, DECREASE)
- status: CharField (choices: ACTIVE, COMPLETED, ARCHIVED)

Example:
- reporting_frequency: QUARTERLY
- baseline_year: 2025, baseline_value: 100
- target_year: 2028, target_value: 50
- Result: Track progress across 16 quarters (Q1-Q4 × 4 years)
```

**Dynamic Period Resolution:**
- Target no longer stores single ReportingPeriod FK
- Instead, system dynamically resolves all periods matching:
  - `frequency = target.reporting_frequency`
  - `year range = baseline_year to target_year`

#### 2. **Multi-Year Reporting Frequency Architecture**

**Problem Solved:**
```
Old approach: Target tied to SINGLE ReportingPeriod
Issue: Can't span multiple years or change frequency without re-creating target

New approach: Target specifies FREQUENCY not specific periods
Benefit: System auto-generates periods as needed
```

**Example Scenario:**

```
Target: Reduce waste quarterly from 2025-2028

Inputs:
{
  "indicator_id": "waste-uuid",
  "reporting_frequency": "QUARTERLY",
  "baseline_year": 2025, baseline_value: 100,
  "target_year": 2028, target_value": 50
}

Backend Process:
1. Create TargetGoal with frequency=QUARTERLY
2. When calculating progress:
   - Call get_target_reporting_periods(goal)
   - System queries for ALL quarterly periods 2025-2028
   - If any missing, auto-generates them via ensure_reporting_periods_exist()
   - Returns: [Q1-2025, Q2-2025, ..., Q4-2028] = 16 periods
3. Fetch DataSubmission across all 16 periods
4. Calculate current value: SUM(submissions)
5. Compute progress: (baseline - current) / (baseline - target)

Result:
Current value: 55
Progress: (100 - 55) / (100 - 50) = 90%
Status: on_track (>70%)
```

#### 3. **Reporting Period Auto-Generation Service**

**Location**: `services/reporting_period_service.py`

```python
ensure_reporting_periods_exist(
    organization,
    start_year: int,
    end_year: int,
    frequency: str
) -> int (count of created periods)

Behavior:
1. Query existing periods for org + frequency
2. Identify missing years
3. For each missing year:
   - Call generate_reporting_periods() for that year
   - Create 12, 26, 52, or 365 periods depending on frequency
4. Return count of newly created periods
5. Gracefully handle failures (log warning, continue)

Example:
ensure_reporting_periods_exist(
    organization=org,
    start_year=2025,
    end_year=2028,
    frequency="QUARTERLY"
)
Result: If Q1-Q4 don't exist for 2025, 2026, 2027, 2028,
        they are created (16 periods total)
```

#### 4. **Selectors** (`selectors/`)

```python
get_target_reporting_periods(goal: TargetGoal) -> List[ReportingPeriod]
    1. Calls ensure_reporting_periods_exist() to auto-generate missing periods
    2. Filters periods by:
       - organization = goal.organization
       - period_type = goal.reporting_frequency
       - start_date__year >= goal.baseline_year
       - end_date__year <= goal.target_year
       - is_active = True
    3. Returns ordered by start_date
    
    Example: Quarterly 2025-2028 returns 16 periods

get_target_progress(goal: TargetGoal) -> dict
    Returns:
    {
        "progress_percent": 0-100,
        "status": "pending|at_risk|on_track|achieved",
        "current_value": float,
        "target_value": float,
        "baseline_value": float
    }
```

#### 5. **API Views & Serializers** (`api/`)

**Serializers:**

```python
TargetGoalCreateSerializer
    Input (frontend sends):
    {
        "indicator_id": "ind-uuid",
        "reporting_frequency": "QUARTERLY",
        "baseline_year": 2025,
        "baseline_value": 100,
        "target_year": 2028,
        "target_value": 50,
        "direction": "decrease",
        "name": "Reduce Waste"
    }

TargetGoalPatchSerializer
    Input (update):
    {
        "reporting_frequency": "SEMI_ANNUAL",
        "target_year": 2029
    }
```

**Views:**

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v1/targets/goals/` | GET/POST | List/Create targets |
| `/api/v1/targets/goals/{id}/` | GET/PATCH/DELETE | Target CRUD |
| `/api/v1/targets/goals/{id}/progress/` | GET | Get progress metrics |

**GoalProgressView (GET /api/v1/targets/goals/{id}/progress/)**
```json
Response:
{
  "progress": {
    "progress_percent": 45,
    "status": "on_track",
    "current_value": 55,
    "target_value": 50,
    "baseline_value": 100,
    "periods_tracked": 16,
    "periods_with_data": 12
  }
}
```

#### 6. **Progress Status Logic**

```python
Status determination:
- "pending": No data submitted yet (current == baseline)
- "achieved": Progress >= 100%
- "on_track": Progress >= 70% (configurable threshold)
- "at_risk": Progress < 70%
```

---

## Submissions & Reporting

### Location
`src/submissions/` app

### Components

#### 1. **DataSubmission Model** (`models/submission.py`)

```python
Fields:
- organization: ForeignKey (Organization)
- indicator: ForeignKey (Indicator)
- reporting_period: ForeignKey (ReportingPeriod)
- facility: ForeignKey (Facility, optional)
- value: FloatField
- unit: CharField
- data_quality: CharField (choices: RAW, VALIDATED, CERTIFIED)
- comment: TextField (optional)
- submitted_by: ForeignKey (User)
- submitted_at: DateTimeField
- created_at: DateTimeField
- updated_at: DateTimeField

Constraints:
- (organization, indicator, reporting_period, facility) must be unique
  Or: One submission per indicator-period-facility combination
  (Can't submit duplicate data for same indicator/period/facility)
```

#### 2. **ReportingPeriod Model**

```python
Generated automatically by system, not user-created

Fields:
- organization: ForeignKey (Organization)
- period_type: CharField (DAILY, WEEKLY, MONTHLY, QUARTERLY, ANNUAL)
- name: CharField (e.g., "Q1 2025", "January 2025")
- start_date: DateField
- end_date: DateField
- is_active: BooleanField
- created_at: DateTimeField

Uniqueness:
- (organization, period_type, start_date, end_date) together must be unique
```

#### 3. **Automatic Period Generation** (`services/period_generation.py`)

```python
generate_reporting_periods(organization, frequency: str, year: int)
    Generates periods for a given year and frequency
    
    Example: MONTHLY 2025 creates 12 periods (Jan-Dec 2025)
    Example: QUARTERLY 2025 creates 4 periods (Q1-Q4 2025)

Auto-triggered when:
- Target is created with multi-year range
- Submission is made for period that doesn't exist yet
```

#### 4. **Services** (`services/`)

```python
submit_data(
    organization,
    indicator,
    reporting_period,
    value,
    facility=None,
    data_quality="RAW",
    submitted_by=None
)
    Creates or updates DataSubmission
    Triggers update_indicator_value() signal
    Returns created submission

get_submission_for_period(indicator, period, facility=None)
    Retrieves or None
```

#### 5. **API Views**

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v1/submissions/` | GET | List submissions |
| `/api/v1/submissions/submit/` | POST | Submit data |
| `/api/v1/submissions/{id}/` | GET/PATCH/DELETE | Submission CRUD |
| `/api/v1/submissions/batch-submit/` | POST | Bulk submit |

**SubmitDataView (POST /api/v1/submissions/submit/)**
```json
Request:
{
  "indicator_id": "ind-uuid",
  "reporting_period_id": "period-uuid",
  "facility_id": "fac-uuid",
  "value": 150.5,
  "unit": "tonnes",
  "data_quality": "VALIDATED"
}

Response 201:
{
  "submission_id": "sub-uuid",
  "created_at": "2026-04-11T...",
  "indicator_value_updated": true
}
```

---

## Compliance Framework

### Location
`src/compliance/` app

### Components

#### 1. **Compliance Models**

**Framework Model** (e.g., Nigeria ESG Code, ISSB, TCFD)
```python
Fields:
- code: CharField (unique, e.g., "NIGERIAN-ESG", "ISSB", "TCFD")
- name: CharField
- description: TextField
- version: CharField
- is_active: BooleanField
```

**ComplianceRequirement Model**
```python
Fields:
- framework: ForeignKey (Framework)
- code: CharField (e.g., "REQ-001")
- title: CharField
- description: TextField
- category: CharField (environmental, social, governance)
- applicable_sectors: JSONField (array of sectors)
- indicators: M2M (which indicators satisfy this requirement)
- is_active: BooleanField
```

**ComplianceStatus Model** (Track org's compliance per requirement)
```python
Fields:
- organization: ForeignKey
- requirement: ForeignKey
- status: CharField (choices: NOT_APPLICABLE, PENDING, IN_PROGRESS, COMPLIANT, NON_COMPLIANT)
- evidence_document: FileField (audit trail)
- last_reviewed_at: DateTimeField
- reviewed_by: ForeignKey (User)
- notes: TextField
```

#### 2. **Services** (`services/`)

```python
update_compliance_status(
    organization,
    requirement,
    status: str,
    evidence=None
)
    Updates compliance status with audit trail
    Auto-calculates org-wide compliance score

calculate_compliance_score(organization, framework=None)
    Returns: 0-100% compliance
    Formula: (COMPLIANT / TOTAL_APPLICABLE) × 100
```

#### 3. **API Views**

| Endpoint | Method |
|----------|--------|
| `/api/v1/compliance/frameworks/` | GET |
| `/api/v1/compliance/requirements/` | GET |
| `/api/v1/compliance/status/` | GET |
| `/api/v1/compliance/status/{req_id}/` | PATCH |

---

## Dashboard & Analytics

### Location
`src/dashboard/` app

### Components

#### 1. **Dashboard Views**

**ExecDashboardView (GET /api/v1/dashboard/exec/)**
- High-level org metrics
- Target progress summary
- Compliance score
- Top indicators by change

**DepartmentDashboardView (GET /api/v1/dashboard/departments/{dept_id}/)**
- Department-specific metrics
- Facility comparison
- Trend analysis

**IndicatorChartView (GET /api/v1/dashboard/indicators/{id}/chart/)**
- Historical data points
- Trend line (linear regression)
- Forecast (extrapolation)

#### 2. **Data Aggregation Services**

```python
get_org_metrics(organization, period_range=None)
    Returns aggregated dashboard data

get_indicator_trend(indicator, start_year, end_year)
    Returns time-series data for charting
    Points: one per reporting period

calculate_trend_forecast(values, forecast_months=12)
    Linear regression + extrapolation
    Returns future values
```

---

## Activities & Emissions

### Location
`src/activities/` app

### Components

#### 1. **Activity Models** (`models/`)

**ActivityType Model**
```python
Fields:
- code: CharField (e.g., "DIESEL-COMB", "ELEC-USAGE")
- name: CharField
- description: TextField
- unit: CharField (e.g., "litres", "kWh")
- indicator: ForeignKey (Indicator, nullable)
  - Links activity to derived indicator (e.g., Diesel → GHG)
- default_emission_factor: DecimalField (optional)
- is_active: BooleanField

Relationship:
- If indicator set: Activity-based collection
- If indicator null: Direct activity tracking (no emissions)
```

**ActivitySubmission Model**
```python
Fields:
- organization: ForeignKey
- activity_type: ForeignKey
- reporting_period: ForeignKey
- facility: ForeignKey (optional)
- value: FloatField (e.g., 100 litres of diesel)
- unit: CharField (must match activity_type.unit)
- submitted_by: ForeignKey (User)
- submitted_at: DateTimeField
- created_at: DateTimeField

Signals:
- On creation: submit_activity_value() called
  - If activity_type.indicator exists: Calculate emissions
  - Update linked IndicatorValue
```

#### 2. **Emission Factors**

**EmissionFactor Model** (Optional but recommended)
```python
Fields:
- activity_type: ForeignKey (ActivityType)
- factor_value: DecimalField (e.g., 2.68 kg CO2/L diesel)
- factor_unit: CharField (e.g., "kg CO2 per litre")
- effective_year: IntegerField (2023, 2024, etc.)
- source: CharField (e.g., "IPCC 2021", "EPA")
- is_active: BooleanField

Example:
ActivityType: "Diesel Combustion"
EmissionFactor: 2.68 kg CO2e per litre (IPCC 2021)
```

#### 3. **Services** (`services/`)

```python
submit_activity_value(
    organization,
    activity_type,
    reporting_period,
    value,
    facility=None,
    submitted_by=None
)
    1. Create ActivitySubmission
    2. If activity_type.indicator exists:
       a. Calculate emissions: value × emission_factor
       b. Call update_indicator_value() for emissions indicator
    3. Return submission

calculate_activity_emissions(activity_type, value)
    Gets active emission factor for activity_type
    Returns: value × factor_value
```

#### 4. **API Views**

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v1/activities/types/` | GET | List activity types |
| `/api/v1/activities/submissions/` | GET/POST | Manage submissions |
| `/api/v1/activities/mappings/` | GET | See activity→indicator mappings |

**SubmitActivityView (POST /api/v1/activities/submissions/)**
```json
Request:
{
  "activity_type_id": "act-uuid",
  "reporting_period_id": "period-uuid",
  "facility_id": "fac-uuid",
  "value": 100.0,
  "unit": "litres"
}

Response 201:
{
  "submission_id": "act-sub-uuid",
  "value": 100.0,
  "indicator_value": {
    "indicator_id": "ghg-uuid",
    "calculated_value": 268.0,
    "unit": "kg CO2e"
  }
}
```

---

## Configuration & Settings

### Location
`config/settings/` app

### Components

#### 1. **Settings Files**

**base.py** - Shared across all environments
- Django core settings
- Database
- Installed apps
- Middleware
- JWT, CORS, CSRF config
- Logging
- Email
- OTP config
- Celery config

**local.py** - Development
- DEBUG = True
- SQLite or local PostgreSQL
- Verbose logging

**production.py** - Production
- DEBUG = False
- PostgreSQL
- Static files from S3
- Error reporting
- Security headers

**celery.py** - Async task configuration

#### 2. **Environment Variables** (`.env`)

```bash
# Django
DJANGO_SECRET_KEY=...
DJANGO_DEBUG=False
ALLOWED_HOSTS=api.example.com

# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/totalesg

# Redis/Celery
REDIS_URL=redis://127.0.0.1:6379/1
CELERY_BROKER_URL=$REDIS_URL
CELERY_RESULT_BACKEND=$REDIS_URL

# JWT
JWT_SECRET=...
JWT_ACCESS_LIFETIME_SECONDS=300
JWT_REFRESH_LIFETIME_SECONDS=604800

# Email
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=...
EMAIL_HOST_PASSWORD=...
EMAIL_USE_TLS=True

# CORS/CSRF
CORS_ALLOWED_ORIGINS=http://localhost:3000,https://app.example.com
CSRF_TRUSTED_ORIGINS=...

# OTP
OTP_TTL_SECONDS=3600
OTP_LENGTH=6
OTP_MAX_REQUESTS_PER_HOUR=6

# AWS (optional)
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
AWS_STORAGE_BUCKET_NAME=...
```

---

## Error Handling & Responses

### Location
`src/common/` app

### Components

#### 1. **RFC 7807 Problem Details Format**

All error responses follow RFC 7807 standard:

```json
{
  "type": "https://totalesg360.com/probs/validation-error",
  "title": "Validation Error",
  "detail": "Invalid organization ID format",
  "code": "invalid_uuid",
  "status": 400,
  "instance": "/api/v1/organizations/"
}
```

**Fields:**
- `type` - URL-based error type (allows future documentation)
- `title` - Human-readable error class
- `detail` - Specific error message
- `code` - Machine-readable error code
- `status` - HTTP status code
- `instance` - Request URI that triggered error

#### 2. **Custom Exception Classes** (`exceptions.py`)

```python
DomainException (base)
    ├─ BadRequest
    ├─ Unauthorized
    ├─ Forbidden
    ├─ NotFound
    ├─ ValidationError
    ├─ OrganizationAlreadyExists
    ├─ UserAlreadyExists
    ├─ OrganizationNotFound
    └─ InternalServerError

Usage:
    from common.exceptions import Unauthorized
    raise Unauthorized(detail="Invalid credentials")
```

#### 3. **Exception Handler** (`drf.py`)

Custom DRF exception handler converts all exceptions to RFC 7807 format:

```python
def custom_exception_handler(exc, context):
    """Convert all exceptions to RFC 7807 problem details."""
    # Validation errors → 400
    # Authentication errors → 401
    # Permission errors → 403
    # Not found → 404
    # Domain exceptions → specific status
    # Others → 500
```

#### 4. **Response Helpers** (`api.py`)

```python
success_response(data, status=200)
    Returns 200 OK response
    {
        "success": true,
        "data": {...}
    }

problem_response(problem_detail, status_code=400)
    Returns error response with RFC 7807 format
```

---

## Security & CSRF Protection

### Overview

The API uses **cookie-based JWT authentication** with **CSRF token protection**.

### Why Both JWT + CSRF?

- **JWT** (access_token cookie) - Authenticates the user
- **CSRF token** - Prevents cross-site request forgery attacks

### Standardized CSRF Flow

See [docs/CSRF_STRATEGY.md](docs/CSRF_STRATEGY.md) for complete details.

**Quick Summary:**

```
1️⃣  POST /api/v1/auth/login/
    ← Response: {csrf_token, ...}
    ← Cookies: access_token, refresh_token, csrftoken

2️⃣  Frontend stores csrf_token from response body

3️⃣  POST /api/v1/indicators/ (mutation)
    → Headers: X-CSRFToken: <stored-token>
    → Cookies: auto-sent by browser
    ✅ Django validates header matches cookie

4️⃣  POST /api/v1/auth/refresh/
    ← Response: {csrf_token: "NEW"} (token rotated)
    → Frontend updates stored token

5️⃣  Repeat step 3 with new token
```

### Security Features

✅ **Token Rotation**
- CSRF token rotated on login (prevents fixation)
- Rotated on each refresh (keeps fresh)

✅ **HttpOnly Enforcement**
- `access_token` HttpOnly (XSS protection)
- `refresh_token` HttpOnly (XSS protection)
- `csrftoken` NOT HttpOnly (frontend must read for header)

✅ **SameSite Policy**
- Dev (HTTP): `SameSite=Lax`
- Prod (HTTPS): `SameSite=None` + `Secure=True`

✅ **Cookie Attributes**
- `Secure` flag prevents transmission over HTTP in production
- `HttpOnly` flag prevents JavaScript access for sensitive tokens
- `Path=/` scopes to entire API

---

## API Endpoints Reference

### Authentication Endpoints

```
POST   /api/v1/auth/login/                 Login with email/password
POST   /api/v1/auth/logout/                Logout & revoke tokens
POST   /api/v1/auth/refresh/               Get new access_token
GET    /api/v1/auth/csrf/                  Bootstrap CSRF token
POST   /api/v1/auth/signup/                Create user + org
POST   /api/v1/auth/request-otp/           Request email OTP
POST   /api/v1/auth/verify-otp/            Activate user
POST   /api/v1/auth/request-password-reset/ Request reset OTP
POST   /api/v1/auth/reset-password/        Reset password
POST   /api/v1/auth/change-password/       Change password (authenticated)
GET    /api/v1/auth/countries/             List countries
```

### Organization Endpoints

```
GET    /api/v1/organizations/              List organizations
POST   /api/v1/organizations/              Create organization
GET    /api/v1/organizations/{id}/         Organization detail
PATCH  /api/v1/organizations/{id}/         Update organization
DELETE /api/v1/organizations/{id}/         Delete organization
GET    /api/v1/organizations/{id}/settings/ Get all settings
PATCH  /api/v1/organizations/{id}/settings/general/ Update general settings
PATCH  /api/v1/organizations/{id}/settings/security/ Update security settings
GET    /api/v1/organizations/options/      List sectors, focus types
```

### Indicator Endpoints

```
GET    /api/v1/indicators/                 List indicators
POST   /api/v1/indicators/                 Create indicator
GET    /api/v1/indicators/{id}/            Indicator detail
PATCH  /api/v1/indicators/{id}/            Update indicator
GET    /api/v1/indicators/{id}/values/     Historical values
GET    /api/v1/indicators/batch-values/    Multiple periods
```

### Target Endpoints

```
GET    /api/v1/targets/goals/              List targets
POST   /api/v1/targets/goals/              Create target
GET    /api/v1/targets/goals/{id}/         Target detail
PATCH  /api/v1/targets/goals/{id}/         Update target
DELETE /api/v1/targets/goals/{id}/         Delete target
GET    /api/v1/targets/goals/{id}/progress/ Get progress metrics
```

### Submission Endpoints

```
GET    /api/v1/submissions/                List submissions
POST   /api/v1/submissions/submit/         Submit data
GET    /api/v1/submissions/{id}/           Submission detail
PATCH  /api/v1/submissions/{id}/           Update submission
DELETE /api/v1/submissions/{id}/           Delete submission
POST   /api/v1/submissions/batch-submit/   Bulk submit
```

### Activity Endpoints

```
GET    /api/v1/activities/types/           List activity types
GET    /api/v1/activities/submissions/     List submissions
POST   /api/v1/activities/submissions/     Submit activity
GET    /api/v1/activities/mappings/        Activity→Indicator mappings
```

### Compliance Endpoints

```
GET    /api/v1/compliance/frameworks/      List frameworks
GET    /api/v1/compliance/requirements/    List requirements
GET    /api/v1/compliance/status/          Org compliance status
PATCH  /api/v1/compliance/status/{id}/     Update requirement status
```

### Dashboard Endpoints

```
GET    /api/v1/dashboard/exec/             Executive summary
GET    /api/v1/dashboard/departments/{id}/ Department metrics
GET    /api/v1/dashboard/indicators/{id}/chart/ Indicator chart data
```

---

## Database Schema

### Core Tables

```
users
├─ id (UUID, PK)
├─ email (VARCHAR unique)
├─ password_hash (VARCHAR)
├─ first_name, last_name
├─ is_active
├─ created_at, updated_at

organizations
├─ id (UUID, PK)
├─ name (VARCHAR)
├─ registration_number, registered_name
├─ sector, country
├─ company_size, logo
├─ primary_reporting_focus
├─ is_active
├─ created_at, updated_at

memberships
├─ id (UUID, PK)
├─ organization_id (UUID, FK)
├─ user_id (UUID, FK)
├─ role_id (UUID, FK)
├─ is_active
├─ created_at
│  UNIQUE (organization_id, user_id, role_id)

roles
├─ id (UUID, PK)
├─ organization_id (UUID, FK, nullable for system roles)
├─ code (VARCHAR unique per org)
├─ name, description
├─ is_active, is_system_role
├─ created_at

capabilities
├─ id (UUID, PK)
├─ code (VARCHAR unique, e.g., "indicators.create")
├─ name, category, description

role_capabilities
├─ role_id (UUID, FK)
├─ capability_id (UUID, FK)
│  UNIQUE (role_id, capability_id)

indicators
├─ id (UUID, PK)
├─ organization_id (UUID, FK)
├─ code, name (VARCHAR)
├─ unit, category
├─ collection_method (DIRECT|ACTIVITY)
├─ is_active
├─ created_at, updated_at

target_goals
├─ id (UUID, PK)
├─ organization_id (UUID, FK)
├─ indicator_id (UUID, FK)
├─ reporting_frequency (VARCHAR, ANNUAL|QUARTERLY|etc.)
├─ baseline_year, baseline_value
├─ target_year, target_value
├─ direction (INCREASE|DECREASE)
├─ status (ACTIVE|COMPLETED|ARCHIVED)
├─ created_at, updated_at

reporting_periods
├─ id (UUID, PK)
├─ organization_id (UUID, FK)
├─ period_type (MONTHLY|QUARTERLY|ANNUAL|etc.)
├─ name (VARCHAR)
├─ start_date, end_date
├─ is_active
├─ created_at
│  UNIQUE (organization_id, period_type, start_date, end_date)

data_submissions
├─ id (UUID, PK)
├─ organization_id (UUID, FK)
├─ indicator_id (UUID, FK)
├─ reporting_period_id (UUID, FK)
├─ facility_id (UUID, FK, nullable)
├─ value (FLOAT)
├─ unit (VARCHAR)
├─ data_quality (RAW|VALIDATED|CERTIFIED)
├─ submitted_by_id (UUID, FK)
├─ submitted_at, created_at, updated_at
│  UNIQUE (organization_id, indicator_id, reporting_period_id, facility_id)

indicator_values
├─ id (UUID, PK)
├─ organization_id (UUID, FK)
├─ indicator_id (UUID, FK)
├─ reporting_period_id (UUID, FK)
├─ facility_id (UUID, FK, nullable)
├─ value (FLOAT, aggregated)
├─ metadata (JSONB)
├─ calculated_at
│  INDEX (organization_id, indicator_id, reporting_period_id)

refresh_tokens
├─ id (UUID, PK)
├─ user_id (UUID, FK)
├─ jti (VARCHAR unique)
├─ ip_address, user_agent
├─ is_revoked
├─ created_at
│  INDEX (user_id, jti)
```

---

## Related Documentation

- [CSRF Protection Strategy](docs/CSRF_STRATEGY.md) - Complete authentication & CSRF guide
- [Target Goal Reporting Frequency](docs/TARGETGOAL_REPORTING_FREQUENCY.md) - Multi-year targets
- [Organization Settings](docs/ORGANIZATION_SETTINGS_SUMMARY.md) - Settings implementation
- [Activity-Indicator Integration](docs/INTEGRATION_COMPLETE.md) - Activity-based data flow
- [Reporting Period Auto-Generation](docs/REPORTING_PERIOD_AUTO_GENERATION.md) - Period generation logic
- [Regulatory System](docs/REGULATORY_SYSTEM.md) - Compliance frameworks

---

## Quick Start

### 1. Setup Development Environment

```bash
# Clone repository
git clone ...
cd Totalesg360-backend-API

# Create virtual environment
python3.12 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Setup environment file
cp .env.example .env
# Edit .env with your settings

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Start development server
python manage.py runserver
```

### 2. Test Authentication

```bash
# Get CSRF token before login
curl -X GET http://localhost:8000/api/v1/auth/csrf/

# Login
curl -X POST http://localhost:8000/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"password"}' \
  -c cookies.txt

# Make authenticated request
curl -X GET http://localhost:8000/api/v1/indicators/ \
  -b cookies.txt
```

### 3. Frontend Integration

See [docs/CSRF_STRATEGY.md](docs/CSRF_STRATEGY.md) for:
- JavaScript/Fetch examples
- React hooks
- Axios configuration
- cURL testing

---

## Deployment

### Docker

```bash
# Build image
docker build -t totalesg360 .

# Run container
docker run -p 8000:8000 \
  --env-file .env \
  --volume ./logs:/app/logs \
  totalesg360
```

### Docker Compose

```bash
docker-compose -f docker-compose.prod.yml up -d
```

### Environment Setup (Production)

1. Configure PostgreSQL
2. Configure Redis
3. Set up S3 for static files
4. Configure email service
5. Set `DEBUG=False` in .env
6. Generate new `SECRET_KEY`
7. Run migrations: `python manage.py migrate`
8. Collect static files: `python manage.py collectstatic`

---

## Support & Contact

For questions or issues, please contact the development team or refer to the docs in the `docs/` folder.
