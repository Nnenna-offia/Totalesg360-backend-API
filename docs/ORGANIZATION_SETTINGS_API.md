# Organization Settings API

## Overview

This document describes the Organization Settings API endpoints for managing organization configuration, including general settings, security settings, departments, and framework assignments.

## Architecture

Following the HackSoft pattern:

- Models: `OrganizationSettings`, `Department`, extended `Organization`
- Selectors: functions to retrieve organization settings and related data
- Services: business logic for updating settings
- API Views: REST endpoints for settings management

## Models

### OrganizationSettings

OneToOne relationship with `Organization`. Stores system configuration and preferences.

Fields (high level):

- General Settings: `system_language`, `timezone`, `currency`, `date_format`, `admin_theme`, `notifications_enabled`, `system_update_frequency`, `export_formats`
- Security Settings: `security_checks_frequency`, `require_2fa`, `encrypt_stored_data`, `encryption_method`

### Department

ForeignKey to `Organization`. Represents departments/divisions within an organization.

Fields: `name`, `code`, `description`, `is_active`.

### Organization (Extended)

New fields added: `registered_name`, `registration_number`, `company_size`, `logo`.

---

## API Endpoints

> Note: The API uses the `X-ORG-ID` header to resolve the organization for settings endpoints. Alternatively some endpoints accept `{org_id}` in the path — check the endpoint description for specifics.

### 1) Get Organization Settings

GET `/api/v1/organizations/{org_id}/settings/` or `GET /api/v1/organizations/settings/` (with `X-ORG-ID` header)

Retrieve organization details, settings, departments, and framework assignments.

Permissions: authenticated users

Response example:

```json
{
  "success": true,
  "data": {
    "organization": {
      "id": "uuid",
      "name": "ACME Corp",
      "registered_name": "ACME Corporation Ltd",
      "registration_number": "RC123456",
      "company_size": "medium",
      "logo": "url/to/logo.png",
      "sector": "manufacturing",
      "country": "NG",
      "primary_reporting_focus": "HYBRID",
      "is_active": true
    },
    "settings": {
      "id": "uuid",
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
      "created_at": "2026-03-15T10:00:00Z",
      "updated_at": "2026-03-15T10:00:00Z"
    },
    "departments": [
      {
        "id": "uuid",
        "name": "Operations",
        "code": "OPS",
        "description": "Operations department",
        "is_active": true,
        "created_at": "2026-03-15T10:00:00Z",
        "updated_at": "2026-03-15T10:00:00Z"
      }
    ],
    "frameworks": [
      {
        "id": "uuid",
        "framework": "uuid",
        "framework_name": "GRI Standards",
        "framework_code": "GRI",
        "is_primary": true,
        "is_enabled": true,
        "assigned_at": "2026-03-15T10:00:00Z"
      }
    ]
  }
}
```

### 2) Update General Settings

PATCH `/api/v1/organizations/{org_id}/settings/general/` (or use `X-ORG-ID` header)

Permissions: `org.manage` capability required

Request body (JSON, all fields optional):

```json
{
  "system_language": "en",
  "timezone": "Africa/Lagos",
  "currency": "NGN",
  "date_format": "DD/MM/YYYY",
  "admin_theme": "light",
  "notifications_enabled": true,
  "system_update_frequency": "daily",
  "export_formats": ["pdf", "xlsx", "csv"]
}
```

Response example:

```json
{
  "success": true,
  "message": "General settings updated successfully",
  "data": { /* updated general settings object */ }
}
```

### 3) Update Security Settings

PATCH `/api/v1/organizations/{org_id}/settings/security/` (or use `X-ORG-ID` header)

Permissions: `org.manage` capability required

Request body (JSON, all fields optional):

```json
{
  "security_checks_frequency": "daily",
  "require_2fa": true,
  "encrypt_stored_data": true,
  "encryption_method": "AES-256"
}
```

Response example:

```json
{
  "success": true,
  "message": "Security settings updated successfully",
  "data": { /* updated security object */ }
}
```

## Permission System

Settings update endpoints require the `org.manage` capability.

- Uses `HasCapability` permission class
- Checks user's membership in the organization
- Verifies the membership's role has the required capability

## Field Choices

### System language

- `en`: English
- `fr`: French
- `es`: Spanish

### Timezone

- `UTC`: UTC
- `Africa/Lagos`: West Africa Time (WAT)
- `Africa/Nairobi`: East Africa Time (EAT)
- `America/New_York`: Eastern Standard Time (EST)
- `America/Los_Angeles`: Pacific Standard Time (PST)

### Currency

- `USD`: US Dollar
- `EUR`: Euro
- `GBP`: British Pound
- `NGN`: Nigerian Naira
- `ZAR`: South African Rand

### Date format

- `DD/MM/YYYY`: Day/Month/Year
- `MM/DD/YYYY`: Month/Day/Year
- `YYYY-MM-DD`: Year-Month-Day

### Admin theme

- `light`, `dark`, `auto`

### Update frequency

- `realtime`, `hourly`, `daily`, `weekly`

### Encryption method

- `AES-256`, `AES-128`, `RSA-2048`

### Company size

- `small`, `medium`, `large`, `enterprise`

## Error handling

Endpoints return structured error responses. Example:

```json
{
  "success": false,
  "message": "Error message",
  "errors": {
    "field_name": ["Error details"]
  }
}
```

Common HTTP status codes:

- `200` OK — success
- `400` Bad Request — invalid data or validation error
- `401` Unauthorized — not authenticated
- `403` Forbidden — missing required capability
- `404` Not Found — organization or resource not found

## Database migration

A migration was created and applied to add settings and department tables and extend `Organization`:

- `0004_organization_company_size_organization_logo_and_more.py`

## Usage examples

Get settings (curl):

```bash
curl -X GET \
  'http://localhost:8000/api/v1/organizations/{org_id}/settings/' \
  -H 'Authorization: Bearer {token}'
```

Update general settings (curl):

```bash
curl -X PATCH \
  'http://localhost:8000/api/v1/organizations/{org_id}/settings/general/' \
  -H 'Authorization: Bearer {token}' \
  -H 'Content-Type: application/json' \
  -d '{
    "timezone": "Africa/Lagos",
    "currency": "NGN",
    "notifications_enabled": true
  }'
```

Update security settings (curl):

```bash
curl -X PATCH \
  'http://localhost:8000/api/v1/organizations/{org_id}/settings/security/' \
  -H 'Authorization: Bearer {token}' \
  -H 'Content-Type: application/json' \
  -d '{
    "require_2fa": true,
    "encrypt_stored_data": true
  }'
```

## Notes

- `OrganizationSettings` are automatically created if they don't exist when accessing settings.
- The related_name for `OrganizationSettings` is `system_settings` (not `settings`) to avoid conflict with the existing `settings` JSONField on `Organization`.
- All update operations are wrapped in database transactions for data integrity.
- Field validation is performed at both serializer and service levels.

