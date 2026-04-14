# Organization Creation & API Endpoints Guide

## Table of Contents
1. [Organization Model Overview](#organization-model-overview)
2. [Organization Creation Flow](#organization-creation-flow)
3. [API Endpoints](#api-endpoints)
4. [Request/Response Payloads](#requestresponse-payloads)
5. [Authentication & Authorization](#authentication--authorization)
6. [Error Handling](#error-handling)

---

## Organization Model Overview

### Organization Hierarchy Structure

TotalESG360 supports a hierarchical organization structure:
- **Group**: Parent company (root level)
- **Subsidiary**: Business entities under a parent
- **Facility**: Physical operating sites
- **Department**: Divisions within an organization

```
Group (Parent Organization)
├── Subsidiary 1
│   ├── Business Unit
│   └── Department
├── Subsidiary 2
│   ├── Facility
│   └── Department
└── Department
```

### Organization Model Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | UUID | Yes (auto) | Unique identifier |
| `parent` | ForeignKey | No | Parent organization (for hierarchies) |
| `organization_type` | CharField | Yes | One of: `group`, `subsidiary`, `facility`, `department` |
| `name` | CharField | Yes | Organization display name (max 255 chars) |
| `registered_name` | CharField | No | Official registered company name (max 500 chars) |
| `registration_number` | CharField | No | Company registration/CAC number |
| `company_size` | CharField | No | One of: `small`, `medium`, `large`, `enterprise` |
| `logo` | ImageField | No | Organization logo (PNG/JPG) |
| `sector` | CharField | Yes | Industry sector (manufacturing, oil_gas, finance, etc.) |
| `country` | CountryField | Yes | Country code (e.g., NG, US, GB) |
| `primary_reporting_focus` | CharField | Yes | One of: `NIGERIA`, `INTERNATIONAL`, `HYBRID` |
| `settings` | JSONField | No | Sector-specific configuration |
| `is_active` | BooleanField | Yes | Active status (default: True) |
| `created_at` | DateTimeField | Yes (auto) | Creation timestamp |
| `updated_at` | DateTimeField | Yes (auto) | Last update timestamp |

### Company Size Options

```python
{
    "small": "Small (1-50 employees)",
    "medium": "Medium (51-250 employees)",
    "large": "Large (251-1000 employees)",
    "enterprise": "Enterprise (1000+ employees)"
}
```

### Primary Reporting Focus

| Value | Description |
|-------|-------------|
| `NIGERIA` | Nigeria Regulators Only |
| `INTERNATIONAL` | International Frameworks Only |
| `HYBRID` | Nigeria + International (Hybrid) |

---

## Organization Creation Flow

### Step-by-Step Workflow

#### **Step 1: Get Available Options**
Before creating an organization, retrieve the available sectors and reporting focus options.

```
GET /api/v1/organizations/options/
```

**Response:**
```json
{
    "success": true,
    "data": {
        "sectors": [
            {"value": "manufacturing", "label": "Manufacturing"},
            {"value": "oil_gas", "label": "Oil & Gas"},
            {"value": "finance", "label": "Finance"},
            {"value": "energy", "label": "Energy"},
            {"value": "technology", "label": "Technology"}
        ],
        "primary_reporting_focus": [
            {"value": "NIGERIA", "label": "Nigeria Regulators Only"},
            {"value": "INTERNATIONAL", "label": "International Frameworks Only"},
            {"value": "HYBRID", "label": "Nigeria + International (Hybrid)"}
        ]
    }
}
```

---

#### **Step 2: Create Organization (Subsidiary)**
Create the main organization record as a subsidiary or group.

```
POST /api/v1/organizations/subsidiaries/
```

**Request Headers:**
```
Content-Type: application/json
Authorization: Bearer <JWT_TOKEN>
X-ORG-ID: <PARENT_ORG_ID>  # Only if creating a child organization
```

**Request Body:**
```json
{
    "name": "Dangote Industries Limited",
    "registered_name": "Dangote Industries Plc",
    "registration_number": "RC123456",
    "company_size": "enterprise",
    "sector": "manufacturing",
    "country": "NG",
    "organization_type": "group",
    "primary_reporting_focus": "HYBRID"
}
```

**Response: 201 Created**
```json
{
    "success": true,
    "data": {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "name": "Dangote Industries Limited",
        "registered_name": "Dangote Industries Plc",
        "registration_number": "RC123456",
        "company_size": "enterprise",
        "sector": "manufacturing",
        "country": "NG",
        "organization_type": "group",
        "primary_reporting_focus": "HYBRID",
        "is_active": true,
        "created_at": "2026-04-12T10:30:00Z",
        "updated_at": "2026-04-12T10:30:00Z"
    }
}
```

---

#### **Step 3: Update Organization Profile**
Add profile details like logo, company registration, and operational locations.

```
PATCH /api/v1/organizations/profile/
```

**Request Headers:**
```
Content-Type: multipart/form-data
Authorization: Bearer <JWT_TOKEN>
X-ORG-ID: <ORG_ID>
```

**Request Body:**
```json
{
    "registered_business_name": "Dangote Industries Plc",
    "cac_registration_number": "RC123456",
    "company_size": "enterprise",
    "operational_locations": [
        {
            "name": "Lagos Head Office",
            "address": "123 Lekki Expressway, Lagos",
            "city": "Lagos",
            "state": "Lagos",
            "country": "NG",
            "is_primary": true
        },
        {
            "name": "Ogun Manufacturing Plant",
            "address": "KM 28 Abeokuta Expressway",
            "city": "Ogun",
            "state": "Ogun",
            "country": "NG",
            "is_primary": false
        }
    ],
    "fiscal_year_start_month": 1,
    "fiscal_year_end_month": 12
}
```

**Response: 200 OK**
```json
{
    "success": true,
    "data": {
        "registered_business_name": "Dangote Industries Plc",
        "cac_registration_number": "RC123456",
        "company_size": "enterprise",
        "logo": "https://cdn.example.com/org_logos/550e8400-e29b-41d4.jpg",
        "operational_locations": [
            {
                "name": "Lagos Head Office",
                "address": "123 Lekki Expressway, Lagos",
                "is_primary": true
            },
            {
                "name": "Ogun Manufacturing Plant",
                "address": "KM 28 Abeokuta Expressway",
                "is_primary": false
            }
        ],
        "fiscal_year_start_month": 1,
        "fiscal_year_end_month": 12
    }
}
```

---

#### **Step 4: Configure General Settings**
Set system preferences like language, timezone, currency, and reporting frequency.

```
PATCH /api/v1/organizations/settings/general/
```

**Request Headers:**
```
Content-Type: application/json
Authorization: Bearer <JWT_TOKEN>
X-ORG-ID: <ORG_ID>
```

**Request Body:**
```json
{
    "system_language": "en",
    "timezone": "Africa/Lagos",
    "currency": "NGN",
    "date_format": "DD/MM/YYYY",
    "admin_theme": "light",
    "notifications_enabled": true,
    "system_update_frequency": "monthly",
    "export_formats": ["pdf", "excel", "csv"],
    "local_reporting_frequency": "quarterly",
    "global_reporting_frequency": "annual"
}
```

**Response: 200 OK**
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
        "system_update_frequency": "monthly",
        "export_formats": ["pdf", "excel", "csv"],
        "local_reporting_frequency": "quarterly",
        "global_reporting_frequency": "annual",
        "updated_at": "2026-04-12T10:45:00Z"
    }
}
```

---

#### **Step 5: Configure Security Settings**
Set security policy and compliance requirements.

```
PATCH /api/v1/organizations/settings/security/
```

**Request Headers:**
```
Content-Type: application/json
Authorization: Bearer <JWT_TOKEN>
X-ORG-ID: <ORG_ID>
```

**Request Body:**
```json
{
    "security_checks_frequency": "daily",
    "require_2fa": true,
    "encrypt_stored_data": true,
    "encryption_method": "AES256",
    "auto_compliance_enabled": true
}
```

**Response: 200 OK**
```json
{
    "success": true,
    "data": {
        "security_checks_frequency": "daily",
        "require_2fa": true,
        "encrypt_stored_data": true,
        "encryption_method": "AES256",
        "auto_compliance_enabled": true,
        "updated_at": "2026-04-12T10:50:00Z"
    }
}
```

---

#### **Step 6 (Optional): Create Business Units/Departments**
Structure the organization by creating business units and departments.

**Create Business Unit:**
```
POST /api/v1/organizations/business-units/
```

**Request Body:**
```json
{
    "name": "Manufacturing Division",
    "description": "Primary manufacturing operations"
}
```

**Response: 201 Created**
```json
{
    "success": true,
    "data": {
        "id": "660e8400-e29b-41d4-a716-446655440001",
        "name": "Manufacturing Division",
        "description": "Primary manufacturing operations",
        "created_at": "2026-04-12T11:00:00Z"
    }
}
```

**Create Department:**
```
POST /api/v1/organizations/departments/
```

**Request Body:**
```json
{
    "name": "ESG Compliance Team",
    "code": "ESG-COMP",
    "description": "Handles all ESG/Sustainability compliance",
    "head": "550e8400-e29b-41d4-a716-446655440005"
}
```

**Response: 201 Created**
```json
{
    "success": true,
    "data": {
        "id": "770e8400-e29b-41d4-a716-446655440002",
        "name": "ESG Compliance Team",
        "code": "ESG-COMP",
        "description": "Handles all ESG/Sustainability compliance",
        "head": "550e8400-e29b-41d4-a716-446655440005",
        "head_name": "John Doe",
        "is_active": true,
        "created_at": "2026-04-12T11:05:00Z"
    }
}
```

---

#### **Step 7 (Optional): Assign Regulatory Frameworks**
Assign compliance frameworks to the organization.

```
POST /api/v1/organizations/organization-frameworks/
```

**Request Body:**
```json
{
    "framework_id": "880e8400-e29b-41d4-a716-446655440003",
    "is_primary": true,
    "is_enabled": true
}
```

**Response: 201 Created**
```json
{
    "success": true,
    "data": {
        "id": "990e8400-e29b-41d4-a716-446655440004",
        "framework_id": "880e8400-e29b-41d4-a716-446655440003",
        "framework_name": "GRI Standards",
        "framework_code": "GRI",
        "is_primary": true,
        "is_enabled": true,
        "assigned_at": "2026-04-12T11:10:00Z"
    }
}
```

---

## API Endpoints

### Organization Management

#### 1. List Organizations
```
GET /api/v1/organizations/
```

**Query Parameters:**
- `sector` (optional): Filter by sector
- `is_active` (optional): Filter by active status
- `page` (optional): Pagination page number
- `limit` (optional): Items per page

**Response: 200 OK**
```json
{
    "success": true,
    "data": {
        "count": 5,
        "next": "https://api.example.com/organizations/?page=2",
        "previous": null,
        "results": [
            {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "name": "Dangote Industries Limited",
                "sector": "manufacturing",
                "is_active": true
            }
        ]
    }
}
```

---

#### 2. Create Organization (New Group/Subsidiary)
```
POST /api/v1/organizations/
```

**Request Body:**
```json
{
    "name": "BUA Cement Company",
    "registered_name": "BUA Cement Plc",
    "registration_number": "RC789012",
    "company_size": "enterprise",
    "sector": "manufacturing",
    "country": "NG",
    "organization_type": "group",
    "primary_reporting_focus": "HYBRID"
}
```

**Response: 201 Created**
```json
{
    "success": true,
    "data": {
        "id": "aa0e8400-e29b-41d4-a716-446655440000",
        "name": "BUA Cement Company",
        "organization_type": "group",
        "sector": "manufacturing",
        "is_active": true
    }
}
```

---

#### 3. Get Organization Details
```
GET /api/v1/organizations/{id}/
```

**Response: 200 OK**
```json
{
    "success": true,
    "data": {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "name": "Dangote Industries Limited",
        "registered_name": "Dangote Industries Plc",
        "registration_number": "RC123456",
        "company_size": "enterprise",
        "logo": "https://cdn.example.com/org_logos/550e8400.jpg",
        "sector": "manufacturing",
        "country": "NG",
        "primary_reporting_focus": "HYBRID",
        "is_active": true,
        "created_at": "2026-04-12T10:30:00Z",
        "updated_at": "2026-04-12T10:30:00Z"
    }
}
```

---

#### 4. Update Organization
```
PATCH /api/v1/organizations/{id}/
```

**Request Body:**
```json
{
    "name": "Dangote Industries Ltd (Updated)",
    "primary_reporting_focus": "INTERNATIONAL",
    "is_active": true
}
```

**Response: 200 OK**
```json
{
    "success": true,
    "data": {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "name": "Dangote Industries Ltd (Updated)",
        "primary_reporting_focus": "INTERNATIONAL",
        "is_active": true
    }
}
```

---

#### 5. Delete Organization
```
DELETE /api/v1/organizations/{id}/
```

**Response: 204 No Content**

---

### Organization Profile & Settings

#### 6. Get Organization Profile
```
GET /api/v1/organizations/profile/
```

**Request Headers:**
```
Authorization: Bearer <JWT_TOKEN>
X-ORG-ID: <ORG_ID>
```

**Response: 200 OK**
```json
{
    "success": true,
    "data": {
        "registered_business_name": "Dangote Industries Plc",
        "cac_registration_number": "RC123456",
        "company_size": "enterprise",
        "logo": "https://cdn.example.com/org_logos/550e8400.jpg",
        "operational_locations": [
            {
                "name": "Lagos Head Office",
                "address": "123 Lekki Expressway, Lagos",
                "city": "Lagos",
                "state": "Lagos",
                "country": "NG",
                "is_primary": true
            }
        ],
        "fiscal_year_start_month": 1,
        "fiscal_year_end_month": 12
    }
}
```

---

#### 7. Update Organization Profile
```
PATCH /api/v1/organizations/profile/
```

**Request Headers:**
```
Content-Type: multipart/form-data
Authorization: Bearer <JWT_TOKEN>
X-ORG-ID: <ORG_ID>
```

**Request Body:**
```json
{
    "registered_business_name": "Dangote Industries Limited",
    "cac_registration_number": "RC123456",
    "company_size": "enterprise",
    "fiscal_year_start_month": 1,
    "fiscal_year_end_month": 12
}
```

**Response: 200 OK**

---

#### 8. Get Organization Settings
```
GET /api/v1/organizations/settings/
```

**Request Headers:**
```
Authorization: Bearer <JWT_TOKEN>
X-ORG-ID: <ORG_ID>
```

**Response: 200 OK**
```json
{
    "success": true,
    "data": {
        "organization": {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "name": "Dangote Industries Limited"
        },
        "settings": {
            "system_language": "en",
            "timezone": "Africa/Lagos",
            "currency": "NGN",
            "require_2fa": true,
            "encrypt_stored_data": true
        },
        "departments": [
            {
                "id": "770e8400-e29b-41d4-a716-446655440002",
                "name": "ESG Compliance Team",
                "code": "ESG-COMP"
            }
        ],
        "frameworks": [
            {
                "id": "990e8400-e29b-41d4-a716-446655440004",
                "framework_name": "GRI Standards",
                "is_primary": true
            }
        ]
    }
}
```

---

#### 9. Update General Settings
```
PATCH /api/v1/organizations/settings/general/
```

**Request Headers:**
```
Content-Type: application/json
Authorization: Bearer <JWT_TOKEN>
X-ORG-ID: <ORG_ID>
```

**Request Body:**
```json
{
    "system_language": "en",
    "timezone": "Africa/Lagos",
    "currency": "NGN",
    "date_format": "DD/MM/YYYY",
    "admin_theme": "dark",
    "notifications_enabled": true
}
```

**Response: 200 OK**

---

#### 10. Update Security Settings
```
PATCH /api/v1/organizations/settings/security/
```

**Request Body:**
```json
{
    "security_checks_frequency": "daily",
    "require_2fa": true,
    "encrypt_stored_data": true,
    "encryption_method": "AES256",
    "auto_compliance_enabled": true
}
```

**Response: 200 OK**

---

### Business Units

#### 11. List Business Units
```
GET /api/v1/organizations/business-units/
```

**Response: 200 OK**
```json
{
    "success": true,
    "data": [
        {
            "id": "660e8400-e29b-41d4-a716-446655440001",
            "name": "Manufacturing Division",
            "created_at": "2026-04-12T11:00:00Z"
        }
    ]
}
```

---

#### 12. Create Business Unit
```
POST /api/v1/organizations/business-units/
```

**Request Body:**
```json
{
    "name": "Sales & Distribution",
    "description": "Sales and distribution operations"
}
```

**Response: 201 Created**

---

#### 13. Get Business Unit Details
```
GET /api/v1/organizations/business-units/{id}/
```

**Response: 200 OK**

---

#### 14. Update Business Unit
```
PATCH /api/v1/organizations/business-units/{id}/
```

**Request Body:**
```json
{
    "name": "Sales & Distribution (Updated)",
    "description": "Updated description"
}
```

**Response: 200 OK**

---

#### 15. Delete Business Unit
```
DELETE /api/v1/organizations/business-units/{id}/
```

**Response: 204 No Content**

---

### Departments

#### 16. List Departments
```
GET /api/v1/organizations/departments/
```

**Response: 200 OK**
```json
{
    "success": true,
    "data": [
        {
            "id": "770e8400-e29b-41d4-a716-446655440002",
            "name": "ESG Compliance Team",
            "code": "ESG-COMP"
        }
    ]
}
```

---

#### 17. Create Department
```
POST /api/v1/organizations/departments/
```

**Request Body:**
```json
{
    "name": "Human Resources",
    "code": "HR-001",
    "description": "HR department",
    "head": "550e8400-e29b-41d4-a716-446655440005"
}
```

**Response: 201 Created**

---

#### 18. Get Department Details
```
GET /api/v1/organizations/departments/{id}/
```

**Response: 200 OK**

---

#### 19. Update Department
```
PATCH /api/v1/organizations/departments/{id}/
```

**Request Body:**
```json
{
    "name": "Human Resources Department",
    "head": "550e8400-e29b-41d4-a716-446655440006"
}
```

**Response: 200 OK**

---

#### 20. Delete Department
```
DELETE /api/v1/organizations/departments/{id}/
```

**Response: 204 No Content**

---

### Organization Hierarchy & Subsidiaries

#### 21. Get Organization Hierarchy
```
GET /api/v1/organizations/hierarchy/
```

**Request Headers:**
```
Authorization: Bearer <JWT_TOKEN>
X-ORG-ID: <PARENT_ORG_ID>
```

**Response: 200 OK**
```json
{
    "success": true,
    "data": {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "name": "Dangote Industries Limited",
        "organization_type": "group",
        "subsidiaries": [
            {
                "id": "550e8400-e29b-41d4-a716-446655440001",
                "name": "Dangote Cement (Lagos)",
                "organization_type": "subsidiary",
                "subsidiaries": []
            },
            {
                "id": "550e8400-e29b-41d4-a716-446655440002",
                "name": "Dangote Refinery",
                "organization_type": "facility"
            }
        ]
    }
}
```

---

#### 22. List Subsidiaries
```
GET /api/v1/organizations/subsidiaries/
```

**Query Parameters:**
- `parent_id` (optional): Filter by parent organization

**Response: 200 OK**
```json
{
    "success": true,
    "data": [
        {
            "id": "550e8400-e29b-41d4-a716-446655440001",
            "name": "Dangote Cement (Lagos)",
            "parent": "550e8400-e29b-41d4-a716-446655440000",
            "organization_type": "subsidiary"
        }
    ]
}
```

---

#### 23. Create Subsidiary
```
POST /api/v1/organizations/subsidiaries/
```

**Request Headers:**
```
Authorization: Bearer <JWT_TOKEN>
X-ORG-ID: <PARENT_ORG_ID>
```

**Request Body:**
```json
{
    "name": "Dangote Refinery",
    "registered_name": "Dangote Refinery and Petrochemicals",
    "organization_type": "facility",
    "sector": "oil_gas",
    "country": "NG",
    "company_size": "enterprise",
    "primary_reporting_focus": "HYBRID"
}
```

**Response: 201 Created**
```json
{
    "success": true,
    "data": {
        "id": "550e8400-e29b-41d4-a716-446655440003",
        "name": "Dangote Refinery",
        "parent": "550e8400-e29b-41d4-a716-446655440000",
        "organization_type": "facility",
        "sector": "oil_gas"
    }
}
```

---

#### 24. Get Subsidiary Details
```
GET /api/v1/organizations/subsidiaries/{id}/
```

**Response: 200 OK**

---

#### 25. Update Subsidiary
```
PATCH /api/v1/organizations/subsidiaries/{id}/
```

**Request Body:**
```json
{
    "name": "Dangote Refinery (Updated)",
    "is_active": true
}
```

**Response: 200 OK**

---

#### 26. Delete Subsidiary
```
DELETE /api/v1/organizations/subsidiaries/{id}/
```

**Response: 204 No Content**

---

#### 27. Get Organization Statistics
```
GET /api/v1/organizations/statistics/
```

**Request Headers:**
```
Authorization: Bearer <JWT_TOKEN>
X-ORG-ID: <ORG_ID>
```

**Response: 200 OK**
```json
{
    "success": true,
    "data": {
        "total_subsidiaries": 2,
        "total_business_units": 3,
        "total_departments": 5,
        "total_members": 150,
        "hierarchy_depth": 2
    }
}
```

---

### Options & Metadata

#### 28. Get Organization Options
```
GET /api/v1/organizations/options/
```

**Response: 200 OK**
```json
{
    "success": true,
    "data": {
        "sectors": [
            {"value": "manufacturing", "label": "Manufacturing"},
            {"value": "oil_gas", "label": "Oil & Gas"},
            {"value": "finance", "label": "Finance"}
        ],
        "primary_reporting_focus": [
            {"value": "NIGERIA", "label": "Nigeria Regulators Only"},
            {"value": "INTERNATIONAL", "label": "International Frameworks Only"},
            {"value": "HYBRID", "label": "Nigeria + International (Hybrid)"}
        ]
    }
}
```

---

## Request/Response Payloads

### Complete Organization Creation Payload

**Full Workflow Request Payloads:**

```json
{
    "step_1_create_organization": {
        "endpoint": "POST /api/v1/organizations/",
        "body": {
            "name": "Dangote Industries Limited",
            "registered_name": "Dangote Industries Plc",
            "registration_number": "RC123456",
            "company_size": "enterprise",
            "sector": "manufacturing",
            "country": "NG",
            "organization_type": "group",
            "primary_reporting_focus": "HYBRID"
        }
    },
    
    "step_2_update_profile": {
        "endpoint": "PATCH /api/v1/organizations/profile/",
        "body": {
            "registered_business_name": "Dangote Industries Plc",
            "cac_registration_number": "RC123456",
            "company_size": "enterprise",
            "fiscal_year_start_month": 1,
            "fiscal_year_end_month": 12
        }
    },
    
    "step_3_general_settings": {
        "endpoint": "PATCH /api/v1/organizations/settings/general/",
        "body": {
            "system_language": "en",
            "timezone": "Africa/Lagos",
            "currency": "NGN",
            "date_format": "DD/MM/YYYY",
            "admin_theme": "light",
            "notifications_enabled": true,
            "system_update_frequency": "monthly",
            "local_reporting_frequency": "quarterly",
            "global_reporting_frequency": "annual"
        }
    },
    
    "step_4_security_settings": {
        "endpoint": "PATCH /api/v1/organizations/settings/security/",
        "body": {
            "security_checks_frequency": "daily",
            "require_2fa": true,
            "encrypt_stored_data": true,
            "encryption_method": "AES256",
            "auto_compliance_enabled": true
        }
    }
}
```

---

## Authentication & Authorization

### Required Headers

All endpoints (except `/options/`) require:

```
Authorization: Bearer <JWT_TOKEN>
X-ORG-ID: <ORGANIZATION_UUID>
Content-Type: application/json
```

### Permission Requirements

| Endpoint Group | Required Permission | Capability |
|---|---|---|
| Organization Create/Update | IsAuthenticated | `org.manage` |
| Profile Management | IsOrgMember | `org.manage` |
| Settings Management | IsOrgMember | `org.manage` |
| Business Units | IsOrgMember | `department.manage` |
| Departments | IsOrgMember | `department.manage` |
| Subsidiaries | IsOrgMember | `organization.manage_hierarchy` |
| Hierarchy/Statistics | IsOrgMember | `org.view` |

### Multi-Tenant Organization Pattern

All organization endpoints use **X-ORG-ID** header for multi-tenant operation:

```bash
# Request scoped to specific organization
curl -X GET https://api.example.com/api/v1/organizations/settings/ \
  -H "Authorization: Bearer <JWT_TOKEN>" \
  -H "X-ORG-ID: 550e8400-e29b-41d4-a716-446655440000" \
  -H "Content-Type: application/json"
```

---

## Error Handling

### Standard Error Response Format

```json
{
    "success": false,
    "error": {
        "type": "https://api.example.com/errors/validation-error",
        "title": "Validation Error",
        "detail": "Field 'sector' is required",
        "status": 400,
        "errors": {
            "sector": ["This field is required."]
        }
    }
}
```

### Common Error Codes

| Status | Error | Description |
|---|---|---|
| 400 | Validation Error | Missing or invalid required fields |
| 401 | Unauthorized | Missing or invalid JWT token |
| 403 | Forbidden | Insufficient permissions for this organization |
| 404 | Not Found | Organization or resource not found |
| 409 | Conflict | Duplicate registration number or unique constraint violation |
| 500 | Server Error | Internal server error |

### Validation Examples

**Missing Required Field:**
```json
{
    "success": false,
    "error": {
        "type": "validation-error",
        "title": "Validation Error",
        "detail": "sector field is required",
        "errors": {
            "sector": ["This field is required."]
        }
    }
}
```

**Invalid Sector Choice:**
```json
{
    "success": false,
    "error": {
        "type": "validation-error",
        "detail": "\"invalid_sector\" is not a valid sector choice",
        "errors": {
            "sector": ["Select a valid choice. invalid_sector is not one of the available choices."]
        }
    }
}
```

**Duplicate Registration Number:**
```json
{
    "success": false,
    "error": {
        "type": "conflict",
        "title": "Conflict",
        "detail": "Organization with registration number RC123456 already exists",
        "status": 409
    }
}
```

---

## Example cURL Requests

### Create Organization
```bash
curl -X POST https://api.example.com/api/v1/organizations/ \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc..." \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Dangote Industries Limited",
    "registered_name": "Dangote Industries Plc",
    "registration_number": "RC123456",
    "company_size": "enterprise",
    "sector": "manufacturing",
    "country": "NG",
    "organization_type": "group",
    "primary_reporting_focus": "HYBRID"
  }'
```

### Update Organization Profile
```bash
curl -X PATCH https://api.example.com/api/v1/organizations/profile/ \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc..." \
  -H "X-ORG-ID: 550e8400-e29b-41d4-a716-446655440000" \
  -H "Content-Type: application/json" \
  -d '{
    "registered_business_name": "Dangote Industries Plc",
    "cac_registration_number": "RC123456",
    "company_size": "enterprise"
  }'
```

### Create Department
```bash
curl -X POST https://api.example.com/api/v1/organizations/departments/ \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc..." \
  -H "X-ORG-ID: 550e8400-e29b-41d4-a716-446655440000" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "ESG Compliance Team",
    "code": "ESG-COMP",
    "description": "Handles all ESG compliance"
  }'
```

---

## Related Compliance Endpoints

The organization structure integrates with compliance tracking:

- `GET /api/v1/compliance/organization` - Organization compliance status
- `GET /api/v1/compliance/organization-frameworks/` - Assigned frameworks
- `GET /api/v1/compliance/organization-frameworks/status/` - Framework compliance status
- `POST /api/v1/compliance/readiness/recalculate/` - Recalculate readiness for organization

---

## Best Practices

1. **Call Options First**: Always call `/organizations/options/` to get valid sector and focus choices
2. **Complete Setup**: Configure all settings (profile, general, security) after organization creation
3. **Error Handling**: Always check response `success` field and `error` object
4. **Multi-Tenancy**: Always include `X-ORG-ID` header in scoped requests
5. **Permissions**: Verify user has required capability before making requests
6. **Validation**: Validate client-side before sending requests to reduce API calls
7. **Hierarchy**: For subsidiaries, ensure parent organization exists before creation
8. **Unique Constraints**: Registration numbers must be unique within the system

---

**Last Updated**: April 12, 2026  
**API Version**: v1  
**Documentation Version**: 1.0
