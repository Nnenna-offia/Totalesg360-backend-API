# Comprehensive Organization API Guide

**Last Updated:** April 12, 2026  
**Version:** 1.0  
**API Base URL:** `/api/v1/organizations/`

---

## Table of Contents

1. [Organization Model Structure](#organization-model-structure)
2. [Related Models](#related-models)
3. [API Endpoints](#api-endpoints)
4. [Organization Creation Workflow](#organization-creation-workflow)
5. [Request/Response Examples](#requestresponse-examples)
6. [Validation Rules](#validation-rules)
7. [Permissions & Authorization](#permissions--authorization)

---

## Organization Model Structure

### Core Organization Model

**Location:** `src/organizations/models/organization.py`

The `Organization` model represents a company/entity using the ESG platform and supports a hierarchical structure: Groups → Subsidiaries → Business Units.

#### Model Fields

| Field | Type | Required | Description | Constraints |
|-------|------|----------|-------------|------------|
| `id` | UUID | Yes | Auto-generated primary key | Read-only |
| `parent` | ForeignKey[Organization] | No | Parent organization for hierarchy | Supports circular logic checks; relates to `subsidiaries` |
| `organization_type` | CharField | Yes | Type in hierarchy | Choices: `group`, `subsidiary`, `facility`, `department`; Default: `subsidiary` |
| `name` | CharField | Yes | Organization name | Max 255 characters |
| `registered_name` | CharField | No | Official registered name | Max 500 characters; blank allowed |
| `registration_number` | CharField | No | Company registration number | Max 100 characters; blank allowed |
| `company_size` | CharField | No | Size category | Choices: `small` (1-50), `medium` (51-250), `large` (251-1000), `enterprise` (1000+) |
| `logo` | ImageField | No | Organization logo | Uploads to `organization_logos/`; MIME types supported: JPEG, PNG, GIF, WebP |
| `sector` | CharField | Yes | Business sector | Choices: `manufacturing`, `oil_gas`, `finance` |
| `country` | CountryField | Yes | ISO 3166-1 country | Django countries library; 2-letter code |
| `primary_reporting_focus` | CharField | No | Reporting focus | Choices: `NIGERIA`, `INTERNATIONAL`, `HYBRID`; Default: `NIGERIA` |
| `regulatory_frameworks` | ManyToManyField | No | Assigned frameworks | Through: `OrganizationFramework` |
| `settings` | JSONField | No | Sector-specific config | Default: `{"modules": {}, "sector_defaults": {}}`; Stores scopes, permits, frameworks |
| `is_active` | BooleanField | Yes | Active status | Default: `True` |
| `created_at` | DateTimeField | Yes | Creation timestamp | Auto-set on create |
| `updated_at` | DateTimeField | Yes | Last update timestamp | Auto-updated on save |

#### Organization Type Choices

```
group        → Group / Parent Company
subsidiary   → Subsidiary / Business Unit
facility     → Facility / Operating Site
department   → Department / Division
```

#### Primary Reporting Focus Choices

```
NIGERIA        → Nigeria Regulators Only
INTERNATIONAL  → International Frameworks Only
HYBRID         → Nigeria + International (Hybrid)
```

#### Company Size Choices

```
small        → Small (1-50 employees)
medium       → Medium (51-250 employees)
large        → Large (251-1000 employees)
enterprise   → Enterprise (1000+ employees)
```

#### Sector Choices

```
manufacturing  → Manufacturing
oil_gas        → Oil & Gas
finance        → Finance
```

#### Database Indexes

```python
indexes = [
    models.Index(fields=['sector', 'is_active']),
    models.Index(fields=['primary_reporting_focus']),
    models.Index(fields=['parent']),
    models.Index(fields=['organization_type']),
    models.Index(fields=['parent', 'organization_type']),
]
```

#### Key Methods

| Method | Returns | Description |
|--------|---------|-------------|
| `get_ancestors()` | List[Organization] | Get all parent organizations up the hierarchy |
| `get_descendants(include_self=False)` | List[Organization] | Get all child organizations recursively |
| `hierarchy_level` (property) | int | Depth in hierarchy (0 = root, 1 = child, etc.) |

---

## Related Models

### 1. OrganizationProfile

**Location:** `src/organizations/models/organization_profile.py`

Holds company-specific profile information separated from core settings. OneToOne relationship with Organization.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | UUID | Yes | Primary key |
| `organization` | OneToOneField | Yes | Link to Organization |
| `registered_business_name` | CharField | No | Official registered business name (max 500) |
| `cac_registration_number` | CharField | No | Company registration number/CAC (max 100) |
| `company_size` | CharField | No | Size category (same choices as Organization) |
| `logo` | ImageField | No | Organization logo (uploads to `organization_logos/`) |
| `operational_locations` | JSONField | No | List of operational locations; Default: `[]` |
| `fiscal_year_start_month` | PositiveSmallIntegerField | No | Fiscal year start month (1-12) |
| `fiscal_year_end_month` | PositiveSmallIntegerField | No | Fiscal year end month (1-12) |
| `cac_document` | FileField | No | Uploaded CAC registration document (uploads to `organization_documents/`) |
| `created_at` | DateTimeField | Yes | Creation timestamp |
| `updated_at` | DateTimeField | Yes | Last update timestamp |

### 2. OrganizationSettings

**Location:** `src/organizations/models/organization_settings.py`

Stores system configuration and preferences. OneToOne relationship with Organization (auto-created on first access).

#### General Settings

| Field | Type | Choices/Default | Description |
|-------|------|-----------------|-------------|
| `system_language` | CharField | `en`, `fr`, `es` | Default: `en` (English) |
| `timezone` | CharField | `UTC`, `Africa/Lagos`, `Africa/Nairobi`, `America/New_York`, `America/Los_Angeles` | Default: `UTC` |
| `currency` | CharField | `USD`, `EUR`, `GBP`, `NGN`, `ZAR` | Default: `USD` |
| `date_format` | CharField | `DD/MM/YYYY`, `MM/DD/YYYY`, `YYYY-MM-DD` | Default: `DD/MM/YYYY` |
| `admin_theme` | CharField | `light`, `dark`, `auto` | Default: `light` |
| `notifications_enabled` | BooleanField | - | Default: `True` |
| `system_update_frequency` | CharField | `realtime`, `hourly`, `daily`, `weekly` | Default: `daily` |
| `security_checks_frequency` | CharField | `realtime`, `hourly`, `daily`, `weekly` | Default: `daily` |
| `export_formats` | JSONField | Array of strings | Default: `[]` (e.g., `['pdf', 'xlsx', 'csv']`) |
| `local_reporting_frequency` | CharField | `realtime`, `hourly`, `daily`, `weekly` | Default: `daily` |
| `global_reporting_frequency` | CharField | `realtime`, `hourly`, `daily`, `weekly` | - |

#### Security Settings

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `require_2fa` | BooleanField | `False` | Require two-factor authentication for all users |
| `encrypt_stored_data` | BooleanField | `False` | Encrypt sensitive data at rest |
| `encryption_method` | CharField | `AES-256` | Choices: `AES-256`, `AES-128`, `RSA-2048` |
| `auto_compliance_enabled` | BooleanField | `False` | Enable automatic compliance checking |

### 3. OrganizationFramework

**Location:** `src/organizations/models/organization_framework.py`

Links organizations to regulatory frameworks with audit tracking.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | UUID | Yes | Primary key |
| `organization` | ForeignKey[Organization] | Yes | Parent organization |
| `framework` | ForeignKey[RegulatoryFramework] | Yes | Assigned framework |
| `is_primary` | BooleanField | No | Whether this is the primary reporting framework; Default: `False` |
| `is_enabled` | BooleanField | Yes | Whether framework is actively used; Default: `True` |
| `assigned_at` | DateTimeField | Yes | Timestamp when assigned; Auto-set |
| `assigned_by` | ForeignKey[User] | No | User who assigned framework; Nullable for system assignments |

**Unique Constraint:** `(organization, framework)`  
**Ordering:** `['-is_primary', '-framework__priority', 'framework__name']`

### 4. Department

**Location:** `src/organizations/models/department.py`

Represents a department/division within an organization.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | UUID | Yes | Primary key |
| `organization` | ForeignKey[Organization] | Yes | Parent organization |
| `name` | CharField | Yes | Department name (max 255) |
| `code` | CharField | No | Department code/abbreviation (max 50) |
| `description` | TextField | No | Department description |
| `head` | ForeignKey[User] | No | Department head; Nullable |
| `is_active` | BooleanField | Yes | Department active status; Default: `True` |
| `created_at` | DateTimeField | Yes | Creation timestamp |
| `updated_at` | DateTimeField | Yes | Last update timestamp |

**Unique Constraint:** `(organization, name)`  
**Indexes:**
```python
models.Index(fields=['organization', 'is_active']),
models.Index(fields=['organization']),
```

### 5. BusinessUnit

**Location:** `src/organizations/models/business_unit.py`

Represents a business unit within an organization.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | UUID | Yes | Primary key |
| `organization` | ForeignKey[Organization] | Yes | Parent organization |
| `name` | CharField | Yes | Business unit name (max 255) |
| `created_at` | DateTimeField | Yes | Creation timestamp |
| `updated_at` | DateTimeField | Yes | Last update timestamp |

**Unique Constraint:** `(organization, name)`

### 6. Facility

**Location:** `src/organizations/models/facility.py`

Represents a physical site/branch/plant within an organization. Data submissions can be scoped to a facility.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | UUID | Yes | Primary key |
| `organization` | ForeignKey[Organization] | Yes | Parent organization |
| `name` | CharField | Yes | Facility name (max 255) |
| `location` | CharField | No | Facility location (max 255) |
| `facility_type` | CharField | No | Type: `Plant`, `Branch`, `Office`, `Refinery`, etc. |
| `metadata` | JSONField | No | Additional facility-specific data; Default: `{}` |
| `is_active` | BooleanField | Yes | Active status; Default: `True` |
| `created_at` | DateTimeField | Yes | Creation timestamp |
| `updated_at` | DateTimeField | Yes | Last update timestamp |

**Unique Constraint:** `(organization, name)`

### 7. Membership

**Location:** `src/organizations/models/membership.py`

Joins User to Organization with a Role. Optionally scoped to a Facility and/or pillar/reporting period.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | UUID | Yes | Primary key |
| `user` | ForeignKey[User] | Yes | User in organization |
| `organization` | ForeignKey[Organization] | Yes | Organization |
| `role` | ForeignKey[Role] | Yes | User role in organization |
| `facility` | ForeignKey[Facility] | No | Optional facility scope |
| `scope` | JSONField | No | Optional contextual constraints (pillar, period, etc.); Default: `{}` |
| `is_active` | BooleanField | Yes | Active status; Default: `True` |
| `joined_at` | DateTimeField | Yes | When user joined; Auto-set |
| `added_by` | ForeignKey[User] | No | User who added this member; Audit trail |

**Unique Constraint:** `(user, organization, role)`

### 8. RegulatoryFramework

**Location:** `src/organizations/models/regulatory_framework.py`

System-defined regulatory frameworks and standards (e.g., NESREA, CBN, GRI, ISSB). Admin-configurable, not user-created.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | UUID | Yes | Primary key |
| `code` | CharField | Yes | Unique identifier (e.g., NESREA, GRI, ISSB); Max 50 |
| `name` | CharField | Yes | Full framework name (max 200) |
| `jurisdiction` | CharField | Yes | Regulatory jurisdiction; Choices: `NIGERIA`, `INTERNATIONAL` |
| `description` | TextField | No | Framework description and purpose |
| `sector` | CharField | No | Sector-specific framework (empty for cross-sector); Max 50 |
| `is_active` | BooleanField | Yes | Availability for selection; Default: `True` |
| `priority` | IntegerField | Yes | Display/assignment priority (higher = more important); Default: `0` |
| `created_at` | DateTimeField | Yes | Creation timestamp |
| `updated_at` | DateTimeField | Yes | Last update timestamp |

**Indexes:**
```python
models.Index(fields=['jurisdiction', 'is_active']),
models.Index(fields=['sector', 'is_active']),
```

---

## API Endpoints

### Authentication & Multi-Tenancy

**All endpoints (except `/options/`) require:**

| Header | Value | Required | Description |
|--------|-------|----------|-------------|
| `Authorization` | `Bearer {token}` | Yes | JWT token from authentication |
| `X-ORG-ID` | `{org_uuid}` | Yes | Organization UUID (except for public endpoints) |

**Public Endpoint:**
- `GET /options/` - Does not require authentication

---

### 1. Organization Options

**Endpoint:** `GET /api/v1/organizations/options/`

Returns available options for organization-related forms (sectors, reporting focus choices).

**Authentication:** None (public endpoint)

**Query Parameters:** None

**Response (200 OK):**

```json
{
  "success": true,
  "data": {
    "sectors": [
      {
        "value": "manufacturing",
        "label": "Manufacturing"
      },
      {
        "value": "oil_gas",
        "label": "Oil & Gas"
      },
      {
        "value": "finance",
        "label": "Finance"
      }
    ],
    "primary_reporting_focus": [
      {
        "value": "NIGERIA",
        "label": "Nigeria Regulators Only"
      },
      {
        "value": "INTERNATIONAL",
        "label": "International Frameworks Only"
      },
      {
        "value": "HYBRID",
        "label": "Nigeria + International (Hybrid)"
      }
    ]
  }
}
```

---

### 2. Organization Settings (Retrieve)

**Endpoint:** `GET /api/v1/organizations/settings/`

Retrieves complete organization settings with all related data.

**Authentication:** Required (IsAuthenticated)  
**Permissions:** IsOrgMember (via X-ORG-ID)

**Query Parameters:** None

**Response (200 OK):**

```json
{
  "success": true,
  "data": {
    "organization": {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "name": "Wacot Limited",
      "registered_name": "Wacot Agriculture Company Limited",
      "registration_number": "CAC/BN/1234567",
      "company_size": "large",
      "logo": "https://api.example.com/media/organization_logos/wacot_logo.png",
      "sector": "manufacturing",
      "country": "NG",
      "primary_reporting_focus": "HYBRID",
      "is_active": true
    },
    "settings": {
      "id": "660e8400-e29b-41d4-a716-446655440000",
      "system_language": "en",
      "timezone": "Africa/Lagos",
      "currency": "NGN",
      "date_format": "DD/MM/YYYY",
      "admin_theme": "light",
      "notifications_enabled": true,
      "system_update_frequency": "daily",
      "security_checks_frequency": "daily",
      "export_formats": ["pdf", "xlsx", "csv"],
      "require_2fa": false,
      "encrypt_stored_data": false,
      "encryption_method": "AES-256",
      "local_reporting_frequency": "daily",
      "global_reporting_frequency": "weekly",
      "auto_compliance_enabled": false,
      "created_at": "2025-12-01T10:00:00Z",
      "updated_at": "2025-12-01T10:00:00Z"
    },
    "departments": [
      {
        "id": "770e8400-e29b-41d4-a716-446655440000",
        "organization": "550e8400-e29b-41d4-a716-446655440000",
        "name": "ESG Compliance",
        "code": "ESG-001",
        "description": "Environmental, Social, and Governance compliance",
        "head": "880e8400-e29b-41d4-a716-446655440000",
        "head_name": "John Doe",
        "is_active": true,
        "created_at": "2025-12-01T10:00:00Z",
        "updated_at": "2025-12-01T10:00:00Z"
      }
    ],
    "frameworks": [
      {
        "id": "990e8400-e29b-41d4-a716-446655440000",
        "framework": "1",
        "framework_name": "NESREA",
        "framework_code": "NESREA",
        "is_primary": true,
        "is_enabled": true,
        "assigned_at": "2025-12-01T10:00:00Z"
      }
    ]
  }
}
```

**Error Response (404 Not Found):**

```json
{
  "type": "https://api.example.com/problems/not-found",
  "title": "Organization not found",
  "detail": "Organization not found or X-ORG-ID header missing",
  "code": "org_not_found"
}
```

---

### 3. Update General Settings

**Endpoint:** `PATCH /api/v1/organizations/settings/general/`

Updates general configuration settings for an organization.

**Authentication:** Required (IsAuthenticated)  
**Permissions:** Required - `org.manage` capability  
**HTTP Method:** PATCH (partial update allowed)

**Request Body:**

```json
{
  "system_language": "en",
  "timezone": "Africa/Lagos",
  "currency": "NGN",
  "date_format": "DD/MM/YYYY",
  "admin_theme": "light",
  "notifications_enabled": true,
  "system_update_frequency": "daily",
  "export_formats": ["pdf", "xlsx", "csv"],
  "local_reporting_frequency": "daily",
  "global_reporting_frequency": "weekly"
}
```

**Field Validation:**

| Field | Validation |
|-------|-----------|
| `system_language` | Must be one of: `en`, `fr`, `es` |
| `timezone` | Must be one of: `UTC`, `Africa/Lagos`, `Africa/Nairobi`, `America/New_York`, `America/Los_Angeles` |
| `currency` | Must be one of: `USD`, `EUR`, `GBP`, `NGN`, `ZAR` |
| `date_format` | Must be one of: `DD/MM/YYYY`, `MM/DD/YYYY`, `YYYY-MM-DD` |
| `admin_theme` | Must be one of: `light`, `dark`, `auto` |
| `notifications_enabled` | Must be boolean |
| `system_update_frequency` | Must be one of: `realtime`, `hourly`, `daily`, `weekly` |
| `export_formats` | Must be a list of strings |
| `local_reporting_frequency` | Must be one of: `realtime`, `hourly`, `daily`, `weekly` |
| `global_reporting_frequency` | Must be one of: `realtime`, `hourly`, `daily`, `weekly` |

**Response (200 OK):**

```json
{
  "success": true,
  "data": {
    "id": "660e8400-e29b-41d4-a716-446655440000",
    "system_language": "en",
    "timezone": "Africa/Lagos",
    "currency": "NGN",
    "date_format": "DD/MM/YYYY",
    "admin_theme": "light",
    "notifications_enabled": true,
    "system_update_frequency": "daily",
    "security_checks_frequency": "daily",
    "export_formats": ["pdf", "xlsx", "csv"],
    "require_2fa": false,
    "encrypt_stored_data": false,
    "encryption_method": "AES-256",
    "local_reporting_frequency": "daily",
    "global_reporting_frequency": "weekly",
    "auto_compliance_enabled": false,
    "created_at": "2025-12-01T10:00:00Z",
    "updated_at": "2025-12-01T10:00:00Z"
  },
  "meta": {
    "message": "General settings updated successfully"
  }
}
```

**Error Response (400 Bad Request - Validation Error):**

```json
{
  "type": "https://api.example.com/problems/validation-error",
  "title": "Validation Error",
  "detail": "Invalid data provided",
  "errors": {
    "timezone": ["Invalid timezone: INVALID_TZ"]
  },
  "code": "validation_error"
}
```

---

### 4. Update Security Settings

**Endpoint:** `PATCH /api/v1/organizations/settings/security/`

Updates security configuration settings for an organization.

**Authentication:** Required (IsAuthenticated)  
**Permissions:** Required - `org.manage` capability  
**HTTP Method:** PATCH (partial update allowed)

**Request Body:**

```json
{
  "security_checks_frequency": "daily",
  "require_2fa": true,
  "encrypt_stored_data": true,
  "encryption_method": "AES-256",
  "auto_compliance_enabled": true
}
```

**Field Validation:**

| Field | Validation |
|-------|-----------|
| `security_checks_frequency` | Must be one of: `realtime`, `hourly`, `daily`, `weekly` |
| `require_2fa` | Must be boolean |
| `encrypt_stored_data` | Must be boolean |
| `encryption_method` | Must be one of: `AES-256`, `AES-128`, `RSA-2048` |
| `auto_compliance_enabled` | Must be boolean |

**Response (200 OK):**

```json
{
  "success": true,
  "data": {
    "id": "660e8400-e29b-41d4-a716-446655440000",
    "system_language": "en",
    "timezone": "Africa/Lagos",
    "currency": "NGN",
    "date_format": "DD/MM/YYYY",
    "admin_theme": "light",
    "notifications_enabled": true,
    "system_update_frequency": "daily",
    "security_checks_frequency": "daily",
    "export_formats": ["pdf", "xlsx", "csv"],
    "require_2fa": true,
    "encrypt_stored_data": true,
    "encryption_method": "AES-256",
    "local_reporting_frequency": "daily",
    "global_reporting_frequency": "weekly",
    "auto_compliance_enabled": true,
    "created_at": "2025-12-01T10:00:00Z",
    "updated_at": "2025-12-01T10:00:00Z"
  },
  "meta": {
    "message": "Security settings updated successfully"
  }
}
```

---

### 5. Organization Profile (Retrieve & Update)

**Endpoints:**
- `GET /api/v1/organizations/profile/` - Retrieve profile
- `PATCH /api/v1/organizations/profile/` - Update profile

**Authentication:** Required (IsAuthenticated)  
**Permissions Required:** `org.manage` capability  
**HTTP Method:** GET / PATCH

**GET Response (200 OK):**

```json
{
  "success": true,
  "data": {
    "registered_business_name": "Wacot Agriculture Company Limited",
    "cac_registration_number": "CAC/BN/1234567",
    "company_size": "large",
    "logo": "https://api.example.com/media/organization_logos/wacot_logo.png",
    "operational_locations": [
      {
        "name": "Headquarters",
        "address": "123 Main Street, Lagos, Nigeria",
        "country": "NG"
      },
      {
        "name": "Manufacturing Plant",
        "address": "456 Industrial Road, Ogun State, Nigeria",
        "country": "NG"
      }
    ],
    "fiscal_year_start_month": 1,
    "fiscal_year_end_month": 12,
    "cac_document": "https://api.example.com/media/organization_documents/wacot_cac.pdf"
  }
}
```

**PATCH Request Body:**

```json
{
  "registered_business_name": "Wacot Agriculture Company Limited",
  "cac_registration_number": "CAC/BN/1234567",
  "company_size": "large",
  "operational_locations": [
    {
      "name": "Headquarters",
      "address": "123 Main Street, Lagos, Nigeria",
      "country": "NG"
    }
  ],
  "fiscal_year_start_month": 1,
  "fiscal_year_end_month": 12
}
```

**PATCH Response (200 OK):**

```json
{
  "success": true,
  "data": {
    "registered_business_name": "Wacot Agriculture Company Limited",
    "cac_registration_number": "CAC/BN/1234567",
    "company_size": "large",
    "logo": "https://api.example.com/media/organization_logos/wacot_logo.png",
    "operational_locations": [
      {
        "name": "Headquarters",
        "address": "123 Main Street, Lagos, Nigeria",
        "country": "NG"
      }
    ],
    "fiscal_year_start_month": 1,
    "fiscal_year_end_month": 12,
    "cac_document": null
  },
  "meta": {
    "message": "Profile updated"
  }
}
```

---

### 6. Business Units - List & Create

**Endpoint:** `GET|POST /api/v1/organizations/business-units/`

Retrieve all business units or create a new business unit for the organization.

**Authentication:** Required (IsAuthenticated)  
**Permissions Required:**
- GET: IsOrgMember
- POST: `org.manage` capability

**GET Response (200 OK):**

```json
{
  "success": true,
  "data": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "name": "Manufacturing Division",
      "created_at": "2025-12-01T10:00:00Z",
      "updated_at": "2025-12-01T10:00:00Z"
    },
    {
      "id": "660e8400-e29b-41d4-a716-446655440000",
      "name": "Supply Chain Division",
      "created_at": "2025-12-01T10:00:00Z",
      "updated_at": "2025-12-01T10:00:00Z"
    }
  ]
}
```

**POST Request Body:**

```json
{
  "name": "Manufacturing Division"
}
```

**POST Response (201 Created):**

```json
{
  "success": true,
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "Manufacturing Division",
    "created_at": "2025-12-01T10:00:00Z",
    "updated_at": "2025-12-01T10:00:00Z"
  }
}
```

---

### 7. Business Units - Retrieve, Update, Delete

**Endpoint:** `GET|PATCH|DELETE /api/v1/organizations/business-units/{pk}/`

Retrieve, update, or delete a specific business unit.

**Authentication:** Required (IsAuthenticated)  
**Permissions Required:** `org.manage` capability  
**Path Parameters:**
- `pk` (UUID) - Business unit ID

**GET Response (200 OK):**

```json
{
  "success": true,
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "Manufacturing Division",
    "created_at": "2025-12-01T10:00:00Z",
    "updated_at": "2025-12-01T10:00:00Z"
  }
}
```

**PATCH Request Body:**

```json
{
  "name": "Production Division (Updated)"
}
```

**PATCH Response (200 OK):**

```json
{
  "success": true,
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "Production Division (Updated)",
    "created_at": "2025-12-01T10:00:00Z",
    "updated_at": "2025-12-01T10:00:00Z"
  }
}
```

**DELETE Response (200 OK):**

```json
{
  "success": true,
  "data": {}
}
```

---

### 8. Departments - List & Create

**Endpoint:** `GET|POST /api/v1/organizations/departments/`

Retrieve all departments or create a new department for the organization.

**Authentication:** Required (IsAuthenticated)  
**Permissions Required:**
- GET: IsOrgMember
- POST: `department.manage` capability

**GET Response (200 OK):**

```json
{
  "success": true,
  "data": [
    {
      "id": "770e8400-e29b-41d4-a716-446655440000",
      "organization": "550e8400-e29b-41d4-a716-446655440000",
      "name": "ESG Compliance",
      "code": "ESG-001",
      "description": "Environmental, Social, and Governance compliance department",
      "head": "880e8400-e29b-41d4-a716-446655440000",
      "head_name": "John Doe",
      "is_active": true,
      "created_at": "2025-12-01T10:00:00Z",
      "updated_at": "2025-12-01T10:00:00Z"
    }
  ]
}
```

**POST Request Body:**

```json
{
  "name": "ESG Compliance",
  "code": "ESG-001",
  "description": "Environmental, Social, and Governance compliance department",
  "head": "880e8400-e29b-41d4-a716-446655440000",
  "is_active": true
}
```

**POST Response (201 Created):**

```json
{
  "success": true,
  "data": {
    "id": "770e8400-e29b-41d4-a716-446655440000",
    "organization": "550e8400-e29b-41d4-a716-446655440000",
    "name": "ESG Compliance",
    "code": "ESG-001",
    "description": "Environmental, Social, and Governance compliance department",
    "head": "880e8400-e29b-41d4-a716-446655440000",
    "head_name": "John Doe",
    "is_active": true,
    "created_at": "2025-12-01T10:00:00Z",
    "updated_at": "2025-12-01T10:00:00Z"
  }
}
```

**POST Error Response (400 Bad Request - Duplicate):**

```json
{
  "type": "https://api.example.com/problems/duplicate-resource",
  "title": "Duplicate Department",
  "detail": "A department with this name already exists in your organization"
}
```

---

### 9. Departments - Retrieve, Update, Delete

**Endpoint:** `GET|PATCH|DELETE /api/v1/organizations/departments/{department_id}/`

Retrieve, update, or delete a specific department.

**Authentication:** Required (IsAuthenticated)  
**Permissions Required:**
- GET: IsOrgMember
- PATCH: `department.manage` capability
- DELETE: `department.manage` capability

**Path Parameters:**
- `department_id` (UUID) - Department ID

**GET Response (200 OK):**

```json
{
  "success": true,
  "data": {
    "id": "770e8400-e29b-41d4-a716-446655440000",
    "organization": "550e8400-e29b-41d4-a716-446655440000",
    "name": "ESG Compliance",
    "code": "ESG-001",
    "description": "Environmental, Social, and Governance compliance department",
    "head": "880e8400-e29b-41d4-a716-446655440000",
    "head_name": "John Doe",
    "is_active": true,
    "created_at": "2025-12-01T10:00:00Z",
    "updated_at": "2025-12-01T10:00:00Z"
  }
}
```

**PATCH Request Body:**

```json
{
  "description": "Updated ESG Compliance department",
  "is_active": true
}
```

**PATCH Response (200 OK):**

```json
{
  "success": true,
  "data": {
    "id": "770e8400-e29b-41d4-a716-446655440000",
    "organization": "550e8400-e29b-41d4-a716-446655440000",
    "name": "ESG Compliance",
    "code": "ESG-001",
    "description": "Updated ESG Compliance department",
    "head": "880e8400-e29b-41d4-a716-446655440000",
    "head_name": "John Doe",
    "is_active": true,
    "created_at": "2025-12-01T10:00:00Z",
    "updated_at": "2025-12-01T10:00:00Z"
  }
}
```

**DELETE Response (204 No Content):**

```
(Empty body)
```

---

### 10. Organization Hierarchy (Tree View)

**Endpoint:** `GET /api/v1/organizations/hierarchy/`

Retrieves the complete hierarchical tree of the user's organization and all its subsidiaries.

**Authentication:** Required (IsAuthenticated)  
**Permissions Required:** IsOrgMember (via X-ORG-ID)

**Query Parameters:** None

**Response (200 OK):**

```json
{
  "success": true,
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "Wacot Group",
    "organization_type": "group",
    "organization_type_display": "Group / Parent Company",
    "sector": "manufacturing",
    "country": "NG",
    "is_active": true,
    "subsidiaries": [
      {
        "id": "660e8400-e29b-41d4-a716-446655440000",
        "name": "Wacot Rice Mills",
        "organization_type": "subsidiary",
        "organization_type_display": "Subsidiary / Business Unit",
        "sector": "manufacturing",
        "country": "NG",
        "is_active": true,
        "subsidiaries": [
          {
            "id": "770e8400-e29b-41d4-a716-446655440000",
            "name": "Lagos Processing Facility",
            "organization_type": "facility",
            "organization_type_display": "Facility / Operating Site",
            "sector": "manufacturing",
            "country": "NG",
            "is_active": true,
            "subsidiaries": []
          }
        ]
      }
    ]
  }
}
```

---

### 11. Subsidiaries - List & Create

**Endpoint:** `GET|POST /api/v1/organizations/subsidiaries/`

Retrieve all direct subsidiaries or create a new subsidiary under the user's organization.

**Authentication:** Required (IsAuthenticated)  
**Permissions Required:**
- GET: IsOrgMember
- POST: `organization.manage_hierarchy` capability

**GET Response (200 OK):**

```json
{
  "success": true,
  "data": [
    {
      "id": "660e8400-e29b-41d4-a716-446655440000",
      "name": "Wacot Rice Mills",
      "registered_name": "Wacot Rice Mills Limited",
      "registration_number": "CAC/BN/7654321",
      "company_size": "large",
      "logo": null,
      "sector": "manufacturing",
      "country": "NG",
      "primary_reporting_focus": "HYBRID",
      "is_active": true
    }
  ]
}
```

**POST Request Body:**

```json
{
  "name": "Wacot Rice Mills",
  "sector": "manufacturing",
  "country": "NG",
  "organization_type": "subsidiary",
  "company_size": "large",
  "registered_name": "Wacot Rice Mills Limited",
  "primary_reporting_focus": "HYBRID"
}
```

**POST Response (201 Created):**

```json
{
  "success": true,
  "data": {
    "id": "660e8400-e29b-41d4-a716-446655440000",
    "name": "Wacot Rice Mills",
    "registered_name": "Wacot Rice Mills Limited",
    "registration_number": "",
    "company_size": "large",
    "logo": null,
    "sector": "manufacturing",
    "country": "NG",
    "primary_reporting_focus": "HYBRID",
    "is_active": true
  }
}
```

---

### 12. Subsidiaries - Retrieve, Update, Delete

**Endpoint:** `GET|PATCH|DELETE /api/v1/organizations/subsidiaries/{sub_id}/`

Retrieve, update, or delete a specific subsidiary organization.

**Authentication:** Required (IsAuthenticated)  
**Permissions Required:**
- GET: IsOrgMember
- PATCH: `organization.manage_hierarchy` capability
- DELETE: `organization.manage_hierarchy` capability

**Path Parameters:**
- `sub_id` (UUID) - Subsidiary organization ID

**GET Response (200 OK):**

```json
{
  "success": true,
  "data": {
    "id": "660e8400-e29b-41d4-a716-446655440000",
    "name": "Wacot Rice Mills",
    "registered_name": "Wacot Rice Mills Limited",
    "registration_number": "CAC/BN/7654321",
    "company_size": "large",
    "logo": null,
    "sector": "manufacturing",
    "country": "NG",
    "primary_reporting_focus": "HYBRID",
    "is_active": true
  }
}
```

**PATCH Request Body:**

```json
{
  "name": "Wacot Rice Mills (Updated)",
  "company_size": "enterprise"
}
```

**PATCH Response (200 OK):**

```json
{
  "success": true,
  "data": {
    "id": "660e8400-e29b-41d4-a716-446655440000",
    "name": "Wacot Rice Mills (Updated)",
    "registered_name": "Wacot Rice Mills Limited",
    "registration_number": "CAC/BN/7654321",
    "company_size": "enterprise",
    "logo": null,
    "sector": "manufacturing",
    "country": "NG",
    "primary_reporting_focus": "HYBRID",
    "is_active": true
  }
}
```

**DELETE Response (204 No Content):**

```
(Empty body)
```

**DELETE Error Response (409 Conflict):**

```json
{
  "type": "https://api.example.com/problems/conflict",
  "title": "Conflict",
  "detail": "Cannot delete subsidiary. It may have dependent data."
}
```

---

### 13. Organization Statistics

**Endpoint:** `GET /api/v1/organizations/statistics/`

Retrieve hierarchy statistics for the user's organization.

**Authentication:** Required (IsAuthenticated)  
**Permissions Required:** IsOrgMember (via X-ORG-ID)

**Query Parameters:** None

**Response (200 OK):**

```json
{
  "success": true,
  "data": {
    "organization_id": "550e8400-e29b-41d4-a716-446655440000",
    "total_descendants": 12,
    "direct_children": 3,
    "depth": 3,
    "organization_type": "group",
    "type_breakdown": {
      "subsidiary": 5,
      "facility": 4,
      "department": 3
    }
  }
}
```

---

## Organization Creation Workflow

### Step-by-Step Creation Process

#### Option 1: Create a Subsidiary Under Existing Organization

**Use Case:** Creating a child organization under an existing parent organization

**Steps:**

1. **Get Organization Options** (optional)
   ```bash
   GET /api/v1/organizations/options/
   ```
   Response contains available sectors and reporting focus options.

2. **Create Subsidiary**
   ```bash
   POST /api/v1/organizations/subsidiaries/
   Headers:
     Authorization: Bearer {token}
     X-ORG-ID: {parent_org_id}
   Body: {
     "name": "Wacot Rice Mills",
     "sector": "manufacturing",
     "country": "NG",
     "organization_type": "subsidiary",
     "company_size": "large",
     "registered_name": "Wacot Rice Mills Limited",
     "primary_reporting_focus": "HYBRID"
   }
   ```

3. **Automatic Settings Inheritance**
   - The new subsidiary automatically inherits organization settings from its parent
   - Settings include language, timezone, currency, etc.
   - An `OrganizationSettings` record is created automatically

4. **Response Contains:**
   - New organization ID
   - All provided fields
   - Inherits parent's `primary_reporting_focus` if not specified

#### Option 2: Set Up Organization Profile

**After creating an organization:**

1. **Update Organization Profile**
   ```bash
   PATCH /api/v1/organizations/profile/
   Headers:
     Authorization: Bearer {token}
     X-ORG-ID: {org_id}
   Body: {
     "registered_business_name": "Wacot Agriculture Company Limited",
     "cac_registration_number": "CAC/BN/1234567",
     "company_size": "large",
     "operational_locations": [...],
     "fiscal_year_start_month": 1,
     "fiscal_year_end_month": 12
   }
   ```

#### Option 3: Configure Organization Settings

**After profile is set up:**

1. **Update General Settings**
   ```bash
   PATCH /api/v1/organizations/settings/general/
   Headers:
     Authorization: Bearer {token}
     X-ORG-ID: {org_id}
   Body: {
     "system_language": "en",
     "timezone": "Africa/Lagos",
     "currency": "NGN",
     "date_format": "DD/MM/YYYY",
     "admin_theme": "light"
   }
   ```

2. **Update Security Settings**
   ```bash
   PATCH /api/v1/organizations/settings/security/
   Headers:
     Authorization: Bearer {token}
     X-ORG-ID: {org_id}
   Body: {
     "require_2fa": true,
     "encrypt_stored_data": true,
     "encryption_method": "AES-256"
   }
   ```

#### Option 4: Create Organizational Structure

**Add departments and business units:**

1. **Create Departments**
   ```bash
   POST /api/v1/organizations/departments/
   Headers:
     Authorization: Bearer {token}
     X-ORG-ID: {org_id}
   Body: {
     "name": "ESG Compliance",
     "code": "ESG-001",
     "description": "ESG compliance department",
     "head": {user_id}
   }
   ```

2. **Create Business Units**
   ```bash
   POST /api/v1/organizations/business-units/
   Headers:
     Authorization: Bearer {token}
     X-ORG-ID: {org_id}
   Body: {
     "name": "Manufacturing Division"
   }
   ```

### Automatic Behaviors During Creation

| Action | Automatic Behavior |
|--------|-------------------|
| Create subsidiary | Inherits settings from parent |
| Create subsidiary | Creates OrganizationSettings record |
| Create child org | Maintains parent-child relationship in DB |
| Create child org | Inherits `primary_reporting_focus` if not specified |

---

## Request/Response Examples

### Complete Organization Creation Example

#### 1. Create Subsidiary Organization

**Request:**
```bash
curl -X POST https://api.example.com/api/v1/organizations/subsidiaries/ \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "X-ORG-ID: 550e8400-e29b-41d4-a716-446655440000" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Wacot Rice Mills",
    "sector": "manufacturing",
    "country": "NG",
    "organization_type": "subsidiary",
    "company_size": "large",
    "registered_name": "Wacot Rice Mills Limited",
    "primary_reporting_focus": "HYBRID"
  }'
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "660e8400-e29b-41d4-a716-446655440000",
    "name": "Wacot Rice Mills",
    "registered_name": "Wacot Rice Mills Limited",
    "registration_number": "",
    "company_size": "large",
    "logo": null,
    "sector": "manufacturing",
    "country": "NG",
    "primary_reporting_focus": "HYBRID",
    "is_active": true
  }
}
```

#### 2. Retrieve Organization Hierarchy

**Request:**
```bash
curl -X GET https://api.example.com/api/v1/organizations/hierarchy/ \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "X-ORG-ID: 550e8400-e29b-41d4-a716-446655440000"
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "Wacot Group",
    "organization_type": "group",
    "organization_type_display": "Group / Parent Company",
    "sector": "manufacturing",
    "country": "NG",
    "is_active": true,
    "subsidiaries": [
      {
        "id": "660e8400-e29b-41d4-a716-446655440000",
        "name": "Wacot Rice Mills",
        "organization_type": "subsidiary",
        "organization_type_display": "Subsidiary / Business Unit",
        "sector": "manufacturing",
        "country": "NG",
        "is_active": true,
        "subsidiaries": []
      }
    ]
  }
}
```

#### 3. Update Organization Settings

**Request:**
```bash
curl -X PATCH https://api.example.com/api/v1/organizations/settings/general/ \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "X-ORG-ID: 660e8400-e29b-41d4-a716-446655440000" \
  -H "Content-Type: application/json" \
  -d '{
    "system_language": "en",
    "timezone": "Africa/Lagos",
    "currency": "NGN",
    "date_format": "DD/MM/YYYY",
    "admin_theme": "light",
    "notifications_enabled": true,
    "system_update_frequency": "daily",
    "export_formats": ["pdf", "xlsx", "csv"],
    "local_reporting_frequency": "daily",
    "global_reporting_frequency": "weekly"
  }'
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "770e8400-e29b-41d4-a716-446655440000",
    "system_language": "en",
    "timezone": "Africa/Lagos",
    "currency": "NGN",
    "date_format": "DD/MM/YYYY",
    "admin_theme": "light",
    "notifications_enabled": true,
    "system_update_frequency": "daily",
    "security_checks_frequency": "daily",
    "export_formats": ["pdf", "xlsx", "csv"],
    "require_2fa": false,
    "encrypt_stored_data": false,
    "encryption_method": "AES-256",
    "local_reporting_frequency": "daily",
    "global_reporting_frequency": "weekly",
    "auto_compliance_enabled": false,
    "created_at": "2025-12-01T10:00:00Z",
    "updated_at": "2025-12-01T10:00:00Z"
  },
  "meta": {
    "message": "General settings updated successfully"
  }
}
```

#### 4. Create a Department

**Request:**
```bash
curl -X POST https://api.example.com/api/v1/organizations/departments/ \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "X-ORG-ID: 660e8400-e29b-41d4-a716-446655440000" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "ESG Compliance",
    "code": "ESG-001",
    "description": "Environmental, Social, and Governance compliance department",
    "head": "880e8400-e29b-41d4-a716-446655440000",
    "is_active": true
  }'
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "990e8400-e29b-41d4-a716-446655440000",
    "organization": "660e8400-e29b-41d4-a716-446655440000",
    "name": "ESG Compliance",
    "code": "ESG-001",
    "description": "Environmental, Social, and Governance compliance department",
    "head": "880e8400-e29b-41d4-a716-446655440000",
    "head_name": "John Doe",
    "is_active": true,
    "created_at": "2025-12-01T10:00:00Z",
    "updated_at": "2025-12-01T10:00:00Z"
  }
}
```

---

## Validation Rules

### Organization Model Validation

| Field | Validation Rule | Example |
|-------|-----------------|---------|
| `name` | Required, max 255 chars | "Wacot Group" |
| `sector` | Required, must match choices | "manufacturing", "oil_gas", "finance" |
| `country` | Required, ISO 3166-1 alpha-2 | "NG", "US", "GB" |
| `organization_type` | Required, must match choices | "group", "subsidiary", "facility", "department" |
| `primary_reporting_focus` | Must match choices or default to NIGERIA | "NIGERIA", "INTERNATIONAL", "HYBRID" |
| `company_size` | Optional, must match choices | "small", "medium", "large", "enterprise" |
| `registered_name` | Optional, max 500 chars | - |
| `registration_number` | Optional, max 100 chars | - |
| `parent` | Optional, cannot create circular hierarchy | Must be different object |

### OrganizationSettings Validation

| Field | Validation Rule |
|-------|-----------------|
| `system_language` | Must be: `en`, `fr`, `es` |
| `timezone` | Must be: `UTC`, `Africa/Lagos`, `Africa/Nairobi`, `America/New_York`, `America/Los_Angeles` |
| `currency` | Must be: `USD`, `EUR`, `GBP`, `NGN`, `ZAR` |
| `date_format` | Must be: `DD/MM/YYYY`, `MM/DD/YYYY`, `YYYY-MM-DD` |
| `admin_theme` | Must be: `light`, `dark`, `auto` |
| `notifications_enabled` | Must be boolean |
| `system_update_frequency` | Must be: `realtime`, `hourly`, `daily`, `weekly` |
| `security_checks_frequency` | Must be: `realtime`, `hourly`, `daily`, `weekly` |
| `export_formats` | Must be a list of strings |
| `require_2fa` | Must be boolean |
| `encrypt_stored_data` | Must be boolean |
| `encryption_method` | Must be: `AES-256`, `AES-128`, `RSA-2048` |

### Department Validation

| Field | Validation Rule | Example |
|-------|-----------------|---------|
| `name` | Required, max 255 chars, unique per organization | "ESG Compliance" |
| `code` | Optional, max 50 chars | "ESG-001" |
| `organization` | Required, must exist | Valid org UUID |
| `head` | Optional, must be valid User | Valid user UUID |
| `is_active` | Optional boolean | `true` |

### Unique Constraints

| Model | Unique Fields | Error Code |
|-------|---------------|-----------|
| Department | (organization, name) | `duplicate-resource` |
| BusinessUnit | (organization, name) | `duplicate-resource` |
| Facility | (organization, name) | `duplicate-resource` |
| OrganizationFramework | (organization, framework) | - |

---

## Permissions & Authorization

### Permission Classes Used

| Permission Class | Description | Endpoints |
|------------------|-------------|-----------|
| `IsAuthenticated` | User must be logged in | Most endpoints |
| `IsOrgMember` | User must be member of org (via X-ORG-ID) | Most org-specific endpoints |
| `HasCapability` | User must have specific role capability | Creation/update/delete endpoints |

### Required Capabilities

| Capability | Required For | Endpoints |
|------------|--------------|-----------|
| `org.manage` | Manage organization settings | PATCH `/settings/general/`, PATCH `/settings/security/`, PATCH `/profile/`, POST `/business-units/` |
| `organization.manage_hierarchy` | Manage org hierarchy | POST `/subsidiaries/`, PATCH `/subsidiaries/{id}/`, DELETE `/subsidiaries/{id}/` |
| `department.manage` | Manage departments | POST `/departments/`, PATCH `/departments/{id}/`, DELETE `/departments/{id}/` |

### Multi-Tenant Context

All organization-scoped endpoints require:

**Header:** `X-ORG-ID: {organization_uuid}`

This header determines which organization context the request operates in. Requests will fail with 404 if:
- Header is missing
- User is not a member of the organization
- Organization does not exist

### Error Codes & Status Codes

| Status | Code | Description |
|--------|------|-------------|
| 200 | OK | Successful retrieval or update |
| 201 | CREATED | Successful resource creation |
| 204 | NO CONTENT | Successful deletion |
| 400 | validation_error | Invalid input data |
| 400 | duplicate-resource | Unique constraint violation |
| 401 | Unauthorized | Missing/invalid authentication token |
| 403 | PermissionDenied | User lacks required capability |
| 404 | not_found | Resource not found or org context missing |
| 409 | conflict | Cannot complete action due to dependent data |
| 500 | internal-error | Unexpected server error |

### Response Format

**Success Response (200, 201):**
```json
{
  "success": true,
  "data": {...},
  "meta": {"message": "..."}
}
```

**Error Response (400, 404, etc.):**
```json
{
  "type": "https://api.example.com/problems/error-type",
  "title": "Error Title",
  "detail": "Error description",
  "code": "error_code",
  "errors": {...} // Only for validation errors
}
```

---

## Summary

### Key Points

1. **Multi-Tenant Architecture:** All endpoints use `X-ORG-ID` header to scope operations to specific organizations

2. **Hierarchical Structure:** Organizations are self-referential, supporting unlimited nesting levels (Groups → Subsidiaries → Facilities)

3. **Settings Inheritance:** When creating subordinate organizations, settings are automatically inherited from parent

4. **Role-Based Access:** All operations are protected by capability-based permissions

5. **Atomic Transactions:** Creation and update operations use database transactions for data consistency

6. **Comprehensive Admin:** Includes organization config, settings, profile, departments, business units, facilities, and regulatory frameworks

### Common Workflows

- **Create Organization Hierarchy:** Create parent → Create subsidiaries → Create facilities
- **Configure Organization:** Set profile → Set general settings → Set security settings
- **Organize Staff:** Create departments → Assign department heads → Create business units
- **Manage Compliance:** Assign regulatory frameworks → Configure framework-specific settings

### API Base URL

```
Base: https://api.example.com/api/v1/organizations/
```

All endpoint paths in this guide are relative to this base URL.

---

**Document Version:** 1.0  
**Last Updated:** April 12, 2026  
**Maintained By:** Development Team
