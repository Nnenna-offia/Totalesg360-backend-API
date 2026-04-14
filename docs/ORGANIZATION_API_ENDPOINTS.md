# Complete Organization API Endpoints

Last Updated: April 12, 2026

This document lists all API endpoints related to organizations across the Totalesg360 backend API.

## Table of Contents
1. [Organization Settings & Metadata](#organization-settings--metadata)
2. [Organization Profile](#organization-profile)
3. [Business Units](#business-units)
4. [Departments](#departments)
5. [Organization Hierarchy](#organization-hierarchy)
6. [Subsidiaries](#subsidiaries)
7. [Organization Statistics](#organization-statistics)
8. [Compliance & Frameworks](#compliance--frameworks)

---

## Organization Settings & Metadata

### Base URL
`/api/v1/organizations/`

### 1. Get Organization Options (Metadata)
**Endpoint:** `GET /api/v1/organizations/options/`

**Description:** Retrieve available options for organization-related forms (sectors, reporting focus types).

**Authentication:** None required (public endpoint)

**Request:**
```
GET /api/v1/organizations/options/
```

**Response:** 200 OK
```json
{
  "success": true,
  "data": {
    "sectors": [
      {"value": "manufacturing", "label": "Manufacturing"},
      {"value": "oil_gas", "label": "Oil & Gas"},
      {"value": "finance", "label": "Finance"},
      {"value": "telecoms", "label": "Telecommunications"}
    ],
    "primary_reporting_focus": [
      {"value": "NIGERIA", "label": "Nigeria Regulators Only"},
      {"value": "INTERNATIONAL", "label": "International Frameworks Only"},
      {"value": "HYBRID", "label": "Nigeria + International (Hybrid)"}
    ]
  }
}
```

**HTTP Status Codes:**
- `200 OK` - Successfully retrieved options

---

### 2. Get Organization Settings
**Endpoint:** `GET /api/v1/organizations/settings/`

**Description:** Retrieve the current organization's complete settings with related data (organization details, settings, departments, frameworks).

**Authentication:** Required (IsAuthenticated)

**Required Headers:**
- `X-ORG-ID: {organization_uuid}` - Organization context

**Request:**
```
GET /api/v1/organizations/settings/
Headers: X-ORG-ID: 660e8400-e29b-41d4-a716-446655440001
```

**Response:** 200 OK
```json
{
  "success": true,
  "data": {
    "organization": {
      "id": "660e8400-e29b-41d4-a716-446655440001",
      "name": "Acme Corporation",
      "sector": "manufacturing",
      "country": "NG"
    },
    "settings": {
      "system_language": "en",
      "timezone": "Africa/Lagos",
      "currency": "NGN",
      "date_format": "DD/MM/YYYY",
      "admin_theme": "light",
      "notifications_enabled": true,
      "system_update_frequency": "daily",
      "export_formats": ["pdf", "xlsx", "csv"],
      "security_checks_frequency": "daily",
      "require_2fa": true,
      "encrypt_stored_data": true,
      "encryption_method": "AES-256"
    },
    "departments": [
      {
        "id": "uuid",
        "name": "Engineering",
        "description": "Engineering department"
      }
    ],
    "frameworks": [
      {
        "id": "uuid",
        "name": "CSRD",
        "code": "EU-CSRD"
      }
    ]
  }
}
```

**HTTP Status Codes:**
- `200 OK` - Settings retrieved successfully
- `404 Not Found` - Organization not found or missing X-ORG-ID header

---

### 3. Update General Settings
**Endpoint:** `PATCH /api/v1/organizations/settings/general/`

**Description:** Update general organization settings (language, timezone, currency, etc.).

**Authentication:** Required (IsAuthenticated, HasCapability)

**Required Capability:** `org.manage`

**Required Headers:**
- `X-ORG-ID: {organization_uuid}` - Organization context

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
  "export_formats": ["pdf", "xlsx", "csv"]
}
```

**Response:** 200 OK
```json
{
  "success": true,
  "data": {
    "system_language": "en",
    "timezone": "Africa/Lagos",
    "currency": "NGN",
    "date_format": "DD/MM/YYYY",
    "admin_theme": "light",
    "notifications_enabled": true,
    "system_update_frequency": "daily",
    "export_formats": ["pdf", "xlsx", "csv"]
  },
  "meta": {
    "message": "General settings updated successfully"
  }
}
```

**HTTP Status Codes:**
- `200 OK` - Settings updated successfully
- `400 Bad Request` - Invalid data or validation error
- `404 Not Found` - Organization not found

**Query Parameters:** None

---

### 4. Update Security Settings
**Endpoint:** `PATCH /api/v1/organizations/settings/security/`

**Description:** Update security settings (2FA requirement, encryption, security check frequency).

**Authentication:** Required (IsAuthenticated, HasCapability)

**Required Capability:** `org.manage`

**Required Headers:**
- `X-ORG-ID: {organization_uuid}` - Organization context

**Request Body:**
```json
{
  "security_checks_frequency": "daily",
  "require_2fa": true,
  "encrypt_stored_data": true,
  "encryption_method": "AES-256"
}
```

**Response:** 200 OK
```json
{
  "success": true,
  "data": {
    "security_checks_frequency": "daily",
    "require_2fa": true,
    "encrypt_stored_data": true,
    "encryption_method": "AES-256"
  },
  "meta": {
    "message": "Security settings updated successfully"
  }
}
```

**HTTP Status Codes:**
- `200 OK` - Settings updated successfully
- `400 Bad Request` - Invalid data
- `404 Not Found` - Organization not found

---

## Organization Profile

### 5. Get Organization Profile
**Endpoint:** `GET /api/v1/organizations/profile/`

**Description:** Retrieve the organization's company profile (logo, CAC number, locations).

**Authentication:** Required (IsAuthenticated)

**Required Headers:**
- `X-ORG-ID: {organization_uuid}` - Organization context

**Request:**
```
GET /api/v1/organizations/profile/
Headers: X-ORG-ID: 660e8400-e29b-41d4-a716-446655440001
```

**Response:** 200 OK
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "organization": {
      "id": "660e8400-e29b-41d4-a716-446655440001",
      "name": "Acme Corporation"
    },
    "logo": "https://cdn.example.com/logos/acme-logo.png",
    "cac_number": "BN2345678",
    "headquarters_address": "123 Business St, Lagos, Nigeria",
    "number_of_locations": 5,
    "registered_employees": 500
  }
}
```

**HTTP Status Codes:**
- `200 OK` - Profile retrieved
- `404 Not Found` - Organization not found

---

### 6. Update Organization Profile
**Endpoint:** `PATCH /api/v1/organizations/profile/`

**Description:** Update organization's company profile information (logo, CAC, locations).

**Authentication:** Required (IsAuthenticated, HasCapability)

**Required Capability:** `org.manage`

**Required Headers:**
- `X-ORG-ID: {organization_uuid}` - Organization context

**Request Body:**
```json
{
  "logo": "/media/org_logos/acme-logo.png",
  "cac_number": "BN2345678",
  "headquarters_address": "123 Business St, Lagos, Nigeria",
  "number_of_locations": 5,
  "registered_employees": 500
}
```

**Response:** 200 OK
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "logo": "/media/org_logos/acme-logo.png",
    "cac_number": "BN2345678",
    "headquarters_address": "123 Business St, Lagos, Nigeria",
    "number_of_locations": 5,
    "registered_employees": 500
  },
  "meta": {
    "message": "Profile updated"
  }
}
```

**HTTP Status Codes:**
- `200 OK` - Profile updated successfully
- `400 Bad Request` - Invalid data
- `404 Not Found` - Organization not found

---

## Business Units

### 7. List Business Units
**Endpoint:** `GET /api/v1/organizations/business-units/`

**Description:** List all business units belonging to the organization.

**Authentication:** Required (IsAuthenticated, HasCapability)

**Required Capability:** `org.manage`

**Required Headers:**
- `X-ORG-ID: {organization_uuid}` - Organization context

**Request:**
```
GET /api/v1/organizations/business-units/
Headers: X-ORG-ID: 660e8400-e29b-41d4-a716-446655440001
```

**Response:** 200 OK
```json
{
  "success": true,
  "data": [
    {
      "id": "uuid",
      "name": "Engineering Division",
      "organization": "660e8400-e29b-41d4-a716-446655440001",
      "created_at": "2024-01-15T10:00:00Z"
    },
    {
      "id": "uuid",
      "name": "Operations Division",
      "organization": "660e8400-e29b-41d4-a716-446655440001",
      "created_at": "2024-01-15T10:05:00Z"
    }
  ]
}
```

**HTTP Status Codes:**
- `200 OK` - Business units retrieved
- `404 Not Found` - Organization not found

---

### 8. Create Business Unit
**Endpoint:** `POST /api/v1/organizations/business-units/`

**Description:** Create a new business unit for the organization.

**Authentication:** Required (IsAuthenticated, HasCapability)

**Required Capability:** `org.manage`

**Required Headers:**
- `X-ORG-ID: {organization_uuid}` - Organization context

**Request Body:**
```json
{
  "name": "New Business Division"
}
```

**Response:** 201 Created
```json
{
  "success": true,
  "data": {
    "id": "new-uuid",
    "name": "New Business Division",
    "organization": "660e8400-e29b-41d4-a716-446655440001",
    "created_at": "2024-01-15T10:10:00Z"
  }
}
```

**HTTP Status Codes:**
- `201 Created` - Business unit created successfully
- `400 Bad Request` - Invalid data
- `404 Not Found` - Organization not found

---

### 9. Get Business Unit Details
**Endpoint:** `GET /api/v1/organizations/business-units/{pk}/`

**Description:** Retrieve details of a specific business unit.

**Authentication:** Required (IsAuthenticated, HasCapability)

**Required Capability:** `org.manage`

**Required Headers:**
- `X-ORG-ID: {organization_uuid}` - Organization context

**Path Parameters:**
- `pk` (UUID) - Business unit ID

**Request:**
```
GET /api/v1/organizations/business-units/550e8400-e29b-41d4-a716-446655440002/
```

**Response:** 200 OK
```json
{
  "success": true,
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440002",
    "name": "Engineering Division",
    "organization": "660e8400-e29b-41d4-a716-446655440001",
    "created_at": "2024-01-15T10:00:00Z"
  }
}
```

**HTTP Status Codes:**
- `200 OK` - Business unit found
- `404 Not Found` - Business unit not found

---

### 10. Update Business Unit
**Endpoint:** `PATCH /api/v1/organizations/business-units/{pk}/`

**Description:** Update an existing business unit.

**Authentication:** Required (IsAuthenticated, HasCapability)

**Required Capability:** `org.manage`

**Required Headers:**
- `X-ORG-ID: {organization_uuid}` - Organization context

**Path Parameters:**
- `pk` (UUID) - Business unit ID

**Request Body:**
```json
{
  "name": "Updated Division Name"
}
```

**Response:** 200 OK
```json
{
  "success": true,
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440002",
    "name": "Updated Division Name",
    "organization": "660e8400-e29b-41d4-a716-446655440001",
    "created_at": "2024-01-15T10:00:00Z"
  }
}
```

**HTTP Status Codes:**
- `200 OK` - Business unit updated
- `400 Bad Request` - Invalid data
- `404 Not Found` - Business unit not found

---

### 11. Delete Business Unit
**Endpoint:** `DELETE /api/v1/organizations/business-units/{pk}/`

**Description:** Delete a business unit.

**Authentication:** Required (IsAuthenticated, HasCapability)

**Required Capability:** `org.manage`

**Required Headers:**
- `X-ORG-ID: {organization_uuid}` - Organization context

**Path Parameters:**
- `pk` (UUID) - Business unit ID

**Request:**
```
DELETE /api/v1/organizations/business-units/550e8400-e29b-41d4-a716-446655440002/
```

**Response:** 200 OK
```json
{
  "success": true,
  "data": {}
}
```

**HTTP Status Codes:**
- `200 OK` - Business unit deleted
- `404 Not Found` - Business unit not found

---

## Departments

### 12. List Departments
**Endpoint:** `GET /api/v1/organizations/departments/`

**Description:** List all departments in the organization (active only).

**Authentication:** Required (IsAuthenticated, IsOrgMember)

**Required Headers:**
- `X-ORG-ID: {organization_uuid}` - Organization context

**Request:**
```
GET /api/v1/organizations/departments/
Headers: X-ORG-ID: 660e8400-e29b-41d4-a716-446655440001
```

**Response:** 200 OK
```json
{
  "success": true,
  "data": [
    {
      "id": "uuid",
      "name": "Human Resources",
      "description": "HR Department",
      "organization": "660e8400-e29b-41d4-a716-446655440001",
      "is_active": true,
      "created_at": "2024-01-15T09:00:00Z"
    },
    {
      "id": "uuid",
      "name": "Finance",
      "description": "Finance Department",
      "organization": "660e8400-e29b-41d4-a716-446655440001",
      "is_active": true,
      "created_at": "2024-01-15T09:05:00Z"
    }
  ]
}
```

**HTTP Status Codes:**
- `200 OK` - Departments retrieved
- `404 Not Found` - Organization not found

---

### 13. Create Department
**Endpoint:** `POST /api/v1/organizations/departments/`

**Description:** Create a new department in the organization.

**Authentication:** Required (IsAuthenticated, IsOrgMember, HasCapability - for POST)

**Required Capability (POST):** `department.manage`

**Required Headers:**
- `X-ORG-ID: {organization_uuid}` - Organization context

**Request Body:**
```json
{
  "name": "Sustainability",
  "description": "Sustainability and ESG initiatives"
}
```

**Response:** 201 Created
```json
{
  "success": true,
  "data": {
    "id": "new-uuid",
    "name": "Sustainability",
    "description": "Sustainability and ESG initiatives",
    "organization": "660e8400-e29b-41d4-a716-446655440001",
    "is_active": true,
    "created_at": "2024-01-15T10:15:00Z"
  }
}
```

**HTTP Status Codes:**
- `201 Created` - Department created successfully
- `400 Bad Request` - Invalid data or duplicate department name
- `404 Not Found` - Organization not found

---

### 14. Get Department Details
**Endpoint:** `GET /api/v1/organizations/departments/{department_id}/`

**Description:** Retrieve details of a specific department.

**Authentication:** Required (IsAuthenticated, IsOrgMember)

**Required Headers:**
- `X-ORG-ID: {organization_uuid}` - Organization context

**Path Parameters:**
- `department_id` (UUID) - Department ID

**Request:**
```
GET /api/v1/organizations/departments/550e8400-e29b-41d4-a716-446655440003/
```

**Response:** 200 OK
```json
{
  "success": true,
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440003",
    "name": "Human Resources",
    "description": "HR Department",
    "organization": "660e8400-e29b-41d4-a716-446655440001",
    "is_active": true,
    "created_at": "2024-01-15T09:00:00Z"
  }
}
```

**HTTP Status Codes:**
- `200 OK` - Department found
- `404 Not Found` - Department or organization not found

---

### 15. Update Department
**Endpoint:** `PATCH /api/v1/organizations/departments/{department_id}/`

**Description:** Update a department's information.

**Authentication:** Required (IsAuthenticated, IsOrgMember, HasCapability)

**Required Capability:** `department.manage`

**Required Headers:**
- `X-ORG-ID: {organization_uuid}` - Organization context

**Path Parameters:**
- `department_id` (UUID) - Department ID

**Request Body:**
```json
{
  "name": "Human Resources & Administration",
  "description": "Updated HR description"
}
```

**Response:** 200 OK
```json
{
  "success": true,
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440003",
    "name": "Human Resources & Administration",
    "description": "Updated HR description",
    "organization": "660e8400-e29b-41d4-a716-446655440001",
    "is_active": true,
    "created_at": "2024-01-15T09:00:00Z"
  }
}
```

**HTTP Status Codes:**
- `200 OK` - Department updated
- `400 Bad Request` - Invalid data or duplicate name
- `404 Not Found` - Department not found

---

### 16. Delete Department
**Endpoint:** `DELETE /api/v1/organizations/departments/{department_id}/`

**Description:** Delete a department (soft delete).

**Authentication:** Required (IsAuthenticated, IsOrgMember, HasCapability)

**Required Capability:** `department.manage`

**Required Headers:**
- `X-ORG-ID: {organization_uuid}` - Organization context

**Path Parameters:**
- `department_id` (UUID) - Department ID

**Request:**
```
DELETE /api/v1/organizations/departments/550e8400-e29b-41d4-a716-446655440003/
```

**Response:** 204 No Content
```
(empty response body)
```

**HTTP Status Codes:**
- `204 No Content` - Department deleted
- `404 Not Found` - Department not found
- `409 Conflict` - Cannot delete (dependent data exists)

---

## Organization Hierarchy

### 17. Get Organization Hierarchy Tree
**Endpoint:** `GET /api/v1/organizations/hierarchy/`

**Description:** Retrieve the complete hierarchical tree of the organization and all subsidiaries in a nested structure. Includes organization type (GROUP, SUBSIDIARY, FACILITY, DEPARTMENT).

**Authentication:** Required (IsAuthenticated, IsOrgMember)

**Required Headers:**
- `X-ORG-ID: {organization_uuid}` - Organization context

**Request:**
```
GET /api/v1/organizations/hierarchy/
Headers: X-ORG-ID: 660e8400-e29b-41d4-a716-446655440001
```

**Response:** 200 OK
```json
{
  "success": true,
  "data": {
    "id": "660e8400-e29b-41d4-a716-446655440001",
    "name": "Acme Group",
    "organization_type": "GROUP",
    "sector": "manufacturing",
    "country": "NG",
    "children": [
      {
        "id": "uuid-subsidiary-1",
        "name": "Acme Manufacturing Ltd",
        "organization_type": "SUBSIDIARY",
        "sector": "manufacturing",
        "country": "NG",
        "children": [
          {
            "id": "uuid-facility-1",
            "name": "Lagos Production Facility",
            "organization_type": "FACILITY",
            "sector": "manufacturing",
            "country": "NG",
            "children": []
          }
        ]
      },
      {
        "id": "uuid-subsidiary-2",
        "name": "Acme Trading Ltd",
        "organization_type": "SUBSIDIARY",
        "sector": "manufacturing",
        "country": "NG",
        "children": []
      }
    ]
  }
}
```

**HTTP Status Codes:**
- `200 OK` - Hierarchy retrieved
- `404 Not Found` - Organization not found
- `500 Internal Server Error` - Error fetching hierarchy

---

## Subsidiaries

### 18. List Subsidiaries
**Endpoint:** `GET /api/v1/organizations/subsidiaries/`

**Description:** List all direct subsidiaries of the organization.

**Authentication:** Required (IsAuthenticated, IsOrgMember)

**Required Headers:**
- `X-ORG-ID: {organization_uuid}` - Organization context

**Request:**
```
GET /api/v1/organizations/subsidiaries/
Headers: X-ORG-ID: 660e8400-e29b-41d4-a716-446655440001
```

**Response:** 200 OK
```json
{
  "success": true,
  "data": [
    {
      "id": "uuid-subsidiary-1",
      "name": "Acme Manufacturing Ltd",
      "organization_type": "SUBSIDIARY",
      "sector": "manufacturing",
      "country": "NG",
      "parent_id": "660e8400-e29b-41d4-a716-446655440001",
      "is_active": true,
      "created_at": "2024-01-15T11:00:00Z"
    },
    {
      "id": "uuid-subsidiary-2",
      "name": "Acme Trading Ltd",
      "organization_type": "SUBSIDIARY",
      "sector": "manufacturing",
      "country": "NG",
      "parent_id": "660e8400-e29b-41d4-a716-446655440001",
      "is_active": true,
      "created_at": "2024-01-15T11:05:00Z"
    }
  ]
}
```

**HTTP Status Codes:**
- `200 OK` - Subsidiaries retrieved
- `404 Not Found` - Organization not found

---

### 19. Create Subsidiary
**Endpoint:** `POST /api/v1/organizations/subsidiaries/`

**Description:** Create a new subsidiary under the parent organization.

**Authentication:** Required (IsAuthenticated, IsOrgMember, HasCapability)

**Required Capability:** `organization.manage_hierarchy`

**Required Headers:**
- `X-ORG-ID: {organization_uuid}` - Parent organization context

**Request Body:**
```json
{
  "name": "Acme Europe Ltd",
  "sector": "manufacturing",
  "country": "GB",
  "organization_type": "subsidiary"
}
```

**Response:** 201 Created
```json
{
  "success": true,
  "data": {
    "id": "new-subsidiary-uuid",
    "name": "Acme Europe Ltd",
    "organization_type": "SUBSIDIARY",
    "sector": "manufacturing",
    "country": "GB",
    "parent_id": "660e8400-e29b-41d4-a716-446655440001",
    "is_active": true,
    "created_at": "2024-01-15T11:10:00Z"
  }
}
```

**HTTP Status Codes:**
- `201 Created` - Subsidiary created successfully
- `400 Bad Request` - Invalid data or validation error
- `404 Not Found` - Parent organization not found
- `500 Internal Server Error` - Error creating subsidiary

**Query Parameters:** None

---

### 20. Get Subsidiary Details
**Endpoint:** `GET /api/v1/organizations/subsidiaries/{sub_id}/`

**Description:** Retrieve details of a specific subsidiary that belongs to the parent organization.

**Authentication:** Required (IsAuthenticated, IsOrgMember)

**Required Headers:**
- `X-ORG-ID: {organization_uuid}` - Parent organization context

**Path Parameters:**
- `sub_id` (UUID) - Subsidiary ID

**Request:**
```
GET /api/v1/organizations/subsidiaries/uuid-subsidiary-1/
Headers: X-ORG-ID: 660e8400-e29b-41d4-a716-446655440001
```

**Response:** 200 OK
```json
{
  "success": true,
  "data": {
    "id": "uuid-subsidiary-1",
    "name": "Acme Manufacturing Ltd",
    "organization_type": "SUBSIDIARY",
    "sector": "manufacturing",
    "country": "NG",
    "parent_id": "660e8400-e29b-41d4-a716-446655440001",
    "is_active": true,
    "created_at": "2024-01-15T11:00:00Z"
  }
}
```

**HTTP Status Codes:**
- `200 OK` - Subsidiary found
- `404 Not Found` - Subsidiary not found or doesn't belong to parent organization

---

### 21. Update Subsidiary
**Endpoint:** `PATCH /api/v1/organizations/subsidiaries/{sub_id}/`

**Description:** Update subsidiary details.

**Authentication:** Required (IsAuthenticated, IsOrgMember, HasCapability)

**Required Capability:** `organization.manage_hierarchy`

**Required Headers:**
- `X-ORG-ID: {organization_uuid}` - Parent organization context

**Path Parameters:**
- `sub_id` (UUID) - Subsidiary ID

**Request Body:**
```json
{
  "name": "Acme Manufacturing Ltd (Updated)",
  "sector": "manufacturing"
}
```

**Response:** 200 OK
```json
{
  "success": true,
  "data": {
    "id": "uuid-subsidiary-1",
    "name": "Acme Manufacturing Ltd (Updated)",
    "organization_type": "SUBSIDIARY",
    "sector": "manufacturing",
    "country": "NG",
    "parent_id": "660e8400-e29b-41d4-a716-446655440001",
    "is_active": true,
    "created_at": "2024-01-15T11:00:00Z"
  }
}
```

**HTTP Status Codes:**
- `200 OK` - Subsidiary updated
- `400 Bad Request` - Invalid data
- `404 Not Found` - Subsidiary not found
- `500 Internal Server Error` - Update error

---

### 22. Delete Subsidiary
**Endpoint:** `DELETE /api/v1/organizations/subsidiaries/{sub_id}/`

**Description:** Delete a subsidiary organization.

**Authentication:** Required (IsAuthenticated, IsOrgMember, HasCapability)

**Required Capability:** `organization.manage_hierarchy`

**Required Headers:**
- `X-ORG-ID: {organization_uuid}` - Parent organization context

**Path Parameters:**
- `sub_id` (UUID) - Subsidiary ID

**Request:**
```
DELETE /api/v1/organizations/subsidiaries/uuid-subsidiary-1/
Headers: X-ORG-ID: 660e8400-e29b-41d4-a716-446655440001
```

**Response:** 204 No Content
```
(empty response body)
```

**HTTP Status Codes:**
- `204 No Content` - Subsidiary deleted
- `404 Not Found` - Subsidiary not found
- `409 Conflict` - Cannot delete (dependent data exists)

---

## Organization Statistics

### 23. Get Organization Statistics
**Endpoint:** `GET /api/v1/organizations/statistics/`

**Description:** Retrieve hierarchy statistics for the organization including metrics like total descendants, direct children count, hierarchy depth, and breakdown by organization type.

**Authentication:** Required (IsAuthenticated, IsOrgMember)

**Required Headers:**
- `X-ORG-ID: {organization_uuid}` - Organization context

**Request:**
```
GET /api/v1/organizations/statistics/
Headers: X-ORG-ID: 660e8400-e29b-41d4-a716-446655440001
```

**Response:** 200 OK
```json
{
  "success": true,
  "data": {
    "organization_id": "660e8400-e29b-41d4-a716-446655440001",
    "organization_name": "Acme Group",
    "total_descendants": 15,
    "direct_children": 3,
    "hierarchy_depth": 4,
    "breakdown_by_type": {
      "GROUP": 1,
      "SUBSIDIARY": 8,
      "FACILITY": 5,
      "DEPARTMENT": 1
    },
    "active_organizations": 14,
    "inactive_organizations": 1
  }
}
```

**HTTP Status Codes:**
- `200 OK` - Statistics retrieved
- `404 Not Found` - Organization not found
- `500 Internal Server Error` - Error calculating statistics

---

## Compliance & Frameworks

Base URL: `/api/v1/compliance/`

### 24. Get Organization Compliance Status
**Endpoint:** `GET /api/v1/compliance/organization`

**Description:** Get overall compliance score and status for the organization across all applicable frameworks.

**Authentication:** Required (IsOrgMember, HasCapability)

**Required Capability:** `compliance.view`

**Required Headers:**
- `X-ORG-ID: {organization_uuid}` - Organization context

**Query Parameters:**
- `period_id` (UUID, required) - Reporting period ID

**Request:**
```
GET /api/v1/compliance/organization?period_id=uuid-period-1
Headers: X-ORG-ID: 660e8400-e29b-41d4-a716-446655440001
```

**Response:** 200 OK
```json
{
  "success": true,
  "data": {
    "organization": {
      "id": "660e8400-e29b-41d4-a716-446655440001",
      "name": "Acme Corporation"
    },
    "period": {
      "id": "uuid-period-1",
      "name": "Q1 2024"
    },
    "overall_compliance_score": 78.5,
    "frameworks": [
      {
        "framework": "CSRD",
        "compliance_score": 75.0,
        "requirements_met": 45,
        "total_requirements": 60
      },
      {
        "framework": "GRI",
        "compliance_score": 82.0,
        "requirements_met": 41,
        "total_requirements": 50
      }
    ]
  }
}
```

**HTTP Status Codes:**
- `200 OK` - Compliance status retrieved
- `400 Bad Request` - Missing period_id parameter
- `404 Not Found` - Organization or reporting period not found

---

### 25. List Organization Frameworks
**Endpoint:** `GET /api/v1/compliance/organization-frameworks/`

**Description:** List all regulatory frameworks assigned to the organization.

**Authentication:** Required (IsOrgMember)

**Required Headers:**
- `X-ORG-ID: {organization_uuid}` - Organization context

**Request:**
```
GET /api/v1/compliance/organization-frameworks/
Headers: X-ORG-ID: 660e8400-e29b-41d4-a716-446655440001
```

**Response:** 200 OK
```json
{
  "success": true,
  "data": [
    {
      "id": "uuid-framework-1",
      "code": "EU-CSRD",
      "name": "Corporate Sustainability Reporting Directive",
      "jurisdiction": "EU",
      "sector": "ALL",
      "is_active": true
    },
    {
      "id": "uuid-framework-2",
      "code": "GRI",
      "name": "Global Reporting Initiative",
      "jurisdiction": "GLOBAL",
      "sector": "ALL",
      "is_active": true
    }
  ]
}
```

**HTTP Status Codes:**
- `200 OK` - Frameworks retrieved
- `400 Bad Request` - Organization context not found

---

### 26. Get Organization Framework Status
**Endpoint:** `GET /api/v1/compliance/organization-frameworks/status/`

**Description:** Get compliance status across all assigned frameworks for the organization.

**Authentication:** Required (IsOrgMember)

**Required Headers:**
- `X-ORG-ID: {organization_uuid}` - Organization context

**Request:**
```
GET /api/v1/compliance/organization-frameworks/status/
Headers: X-ORG-ID: 660e8400-e29b-41d4-a716-446655440001
```

**Response:** 200 OK
```json
[
  {
    "framework": {
      "id": "uuid-framework-1",
      "code": "EU-CSRD",
      "name": "Corporate Sustainability Reporting Directive"
    },
    "status": "IN_PROGRESS",
    "compliance_score": 75.5,
    "indicators_mapped": 45,
    "total_requirements": 60,
    "completion_percentage": 75
  },
  {
    "framework": {
      "id": "uuid-framework-2",
      "code": "GRI",
      "name": "Global Reporting Initiative"
    },
    "status": "COMPLETED",
    "compliance_score": 92.0,
    "indicators_mapped": 50,
    "total_requirements": 50,
    "completion_percentage": 100
  }
]
```

**HTTP Status Codes:**
- `200 OK` - Status retrieved
- `400 Bad Request` - Organization context not found

---

### 27. Get Organization Frameworks with Coverage
**Endpoint:** `GET /api/v1/compliance/organization-frameworks/all/`

**Description:** Get all configured frameworks for the organization with their coverage details.

**Authentication:** Required (IsOrgMember)

**Required Headers:**
- `X-ORG-ID: {organization_uuid}` - Organization context

**Request:**
```
GET /api/v1/compliance/organization-frameworks/all/
Headers: X-ORG-ID: 660e8400-e29b-41d4-a716-446655440001
```

**Response:** 200 OK
```json
[
  {
    "organization_framework": {
      "id": "org-framework-1",
      "is_primary": true,
      "is_enabled": true,
      "assigned_at": "2024-01-10T08:00:00Z"
    },
    "framework": {
      "id": "uuid-framework-1",
      "code": "EU-CSRD",
      "name": "Corporate Sustainability Reporting Directive",
      "jurisdiction": "EU",
      "sector": "ALL"
    },
    "coverage": {
      "total_requirements": 60,
      "requirements_mapped": 45,
      "coverage_percentage": 75.0,
      "requirements_by_pillar": {
        "Environmental": 20,
        "Social": 15,
        "Governance": 10
      },
      "unmapped_requirements": 15
    }
  }
]
```

**HTTP Status Codes:**
- `200 OK` - Frameworks with coverage retrieved
- `400 Bad Request` - Organization context not found

---

## Summary Table

| Endpoint | Method | Authentication | Capability Required | Purpose |
|----------|--------|---|---|---|
| `/organizations/options/` | GET | None | - | Get sectors and reporting focus options |
| `/organizations/settings/` | GET | IsAuthenticated | - | Get all organization settings |
| `/organizations/settings/general/` | PATCH | IsAuthenticated | org.manage | Update general settings |
| `/organizations/settings/security/` | PATCH | IsAuthenticated | org.manage | Update security settings |
| `/organizations/profile/` | GET | IsAuthenticated | - | Get organization profile |
| `/organizations/profile/` | PATCH | IsAuthenticated | org.manage | Update organization profile |
| `/organizations/business-units/` | GET | IsAuthenticated | org.manage | List business units |
| `/organizations/business-units/` | POST | IsAuthenticated | org.manage | Create business unit |
| `/organizations/business-units/{pk}/` | GET | IsAuthenticated | org.manage | Get business unit |
| `/organizations/business-units/{pk}/` | PATCH | IsAuthenticated | org.manage | Update business unit |
| `/organizations/business-units/{pk}/` | DELETE | IsAuthenticated | org.manage | Delete business unit |
| `/organizations/departments/` | GET | IsAuthenticated | - | List departments |
| `/organizations/departments/` | POST | IsAuthenticated | department.manage | Create department |
| `/organizations/departments/{id}/` | GET | IsAuthenticated | - | Get department |
| `/organizations/departments/{id}/` | PATCH | IsAuthenticated | department.manage | Update department |
| `/organizations/departments/{id}/` | DELETE | IsAuthenticated | department.manage | Delete department |
| `/organizations/hierarchy/` | GET | IsAuthenticated | - | Get organization hierarchy tree |
| `/organizations/subsidiaries/` | GET | IsAuthenticated | - | List subsidiaries |
| `/organizations/subsidiaries/` | POST | IsAuthenticated | organization.manage_hierarchy | Create subsidiary |
| `/organizations/subsidiaries/{id}/` | GET | IsAuthenticated | - | Get subsidiary |
| `/organizations/subsidiaries/{id}/` | PATCH | IsAuthenticated | organization.manage_hierarchy | Update subsidiary |
| `/organizations/subsidiaries/{id}/` | DELETE | IsAuthenticated | organization.manage_hierarchy | Delete subsidiary |
| `/organizations/statistics/` | GET | IsAuthenticated | - | Get hierarchy statistics |
| `/compliance/organization` | GET | IsOrgMember | compliance.view | Get compliance status |
| `/compliance/organization-frameworks/` | GET | IsOrgMember | - | List organization frameworks |
| `/compliance/organization-frameworks/status/` | GET | IsOrgMember | - | Get framework status |
| `/compliance/organization-frameworks/all/` | GET | IsOrgMember | - | List all frameworks with coverage |

---

## Authentication & Headers

### Required Headers for Organization Context
All endpoints that operate on a specific organization require the `X-ORG-ID` header:

```
X-ORG-ID: {organization_uuid}
```

**Example:**
```
X-ORG-ID: 660e8400-e29b-41d4-a716-446655440001
```

### User Roles & Capabilities

The system uses capability-based access control with the following organization-specific capabilities:

- `org.manage` - Manage organization settings and profile
- `department.manage` - Create, update, delete departments
- `organization.manage_hierarchy` - Manage subsidiaries and hierarchy
- `compliance.view` - View compliance data

---

## Error Response Format

All endpoints return consistent error responses:

```json
{
  "type": "https://api.totalesg360.com/problems/not-found",
  "title": "Not Found",
  "detail": "The requested resource was not found",
  "code": "resource_not_found",
  "status": 404
}
```

### Common Error Codes
- `org_not_found` - Organization not found or missing X-ORG-ID
- `validation_error` - Invalid request data
- `duplicate_resource` - Resource already exists
- `access_denied` - Insufficient permissions
- `conflict` - Operation conflicts with existing data

---

## Rate Limiting

Organization endpoints are subject to the following rate limits:
- **Default:** 100 requests per minute
- **Authenticated:** 500 requests per minute
- **Rate limit headers:** `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`

---

## Pagination

List endpoints support pagination through query parameters:

- `page` (integer) - Page number (default: 1)
- `page_size` (integer) - Items per page (default: 20, max: 100)

**Example:**
```
GET /api/v1/organizations/departments/?page=2&page_size=50
```

---

## Filtering & Searching

Some list endpoints support filtering and searching:

- `search` - Search in name/code fields
- `sector` - Filter by sector
- `country` - Filter by country
- `is_active` - Filter by active status

**Example:**
```
GET /api/v1/organizations/subsidiaries/?sector=manufacturing&country=NG
```

---

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | April 12, 2026 | Initial documentation for all organization endpoints |

