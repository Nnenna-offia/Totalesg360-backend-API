# Regulatory Coverage & Framework Selection System

## Overview
Configuration-first regulatory compliance system for multi-tenant ESG SaaS platform following HackSoft Django Style Guide.

## Data Models

### RegulatoryFramework (System-Defined)
Location: `src/organizations/models/regulatory_framework.py`

Represents compliance frameworks (NESREA, GRI, ISSB, etc.)
- Admin-configurable, not user-created
- Jurisdiction: NIGERIA | INTERNATIONAL
- Sector-specific or cross-sector
- Priority-based ordering

### OrganizationFramework (M2M Intermediate)
Location: `src/organizations/models/organization_framework.py`

Links organizations to frameworks with audit tracking
- Supports multiple frameworks per organization
- Primary framework designation
- Enable/disable behavior
- Assignment audit trail

### Organization (Updated)
Location: `src/organizations/models/organization.py`

Added fields:
- `regulatory_coverage`: NIGERIA | INTERNATIONAL | HYBRID
- `regulatory_frameworks`: ManyToMany through OrganizationFramework

## Regulatory Coverage States

| Coverage | Meaning | Frameworks Assigned |
|----------|---------|---------------------|
| NIGERIA | Local compliance only | Nigerian frameworks (cross-sector + sector-specific) |
| INTERNATIONAL | Global reporting only | International frameworks (cross-sector) |
| HYBRID | Nigeria + International | Both Nigerian and international frameworks |

## Framework Bootstrapping Logic

Located in: `src/accounts/services/signup.py`

### Assignment Rules:
1. **NIGERIA Coverage**:
   - All Nigerian frameworks where sector="" (cross-sector)
   - All Nigerian frameworks where sector=organization.sector

2. **INTERNATIONAL Coverage**:
   - All international frameworks where sector="" (cross-sector only at signup)

3. **HYBRID Coverage**:
   - Union of NIGERIA + INTERNATIONAL frameworks
   - First assigned framework marked as primary

## Signup Flow

### API Endpoint
```
POST /api/v1/auth/signup/
```

### Request Body
```json
{
  "email": "admin@example.com",
  "password": "securepassword",
  "first_name": "John",
  "last_name": "Doe",
  "organization_name": "Acme Corp",
  "sector": "manufacturing",
  "country": "NG",
  "regulatory_coverage": "HYBRID"
}
```

### Response (201 Created)
```json
{
  "success": true,
  "data": {
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "admin@example.com",
    "organization_id": "660e8400-e29b-41d4-a716-446655440001",
    "organization_name": "Acme Corp",
    "sector": "manufacturing",
    "regulatory_coverage": "HYBRID"
  }
}
```

### Backend Process (Atomic Transaction)
1. Validate inputs (email uniqueness, org name uniqueness, sector, coverage)
2. Create User account
3. Create Organization
4. Assign owner role (org_admin)
5. Create Membership linking user to organization
6. Bootstrap regulatory frameworks based on sector + coverage
7. Return success response

## Seeded Frameworks

### Nigerian Frameworks (6)
- **NESREA**: National Environmental Standards and Regulations Enforcement Agency (cross-sector, priority 100)
- **CBN_ESG**: Central Bank of Nigeria ESG Guidelines (finance sector, priority 90)
- **DPR**: Department of Petroleum Resources (oil_gas sector, priority 90)
- **NUPRC**: Nigerian Upstream Petroleum Regulatory Commission (oil_gas sector, priority 85)
- **FMEnv**: Federal Ministry of Environment (cross-sector, priority 80)
- **NSE_ESG**: Nigerian Exchange ESG Disclosure Guidelines (cross-sector, priority 75)

### International Frameworks (8)
- **GRI**: Global Reporting Initiative Standards (priority 100)
- **ISSB**: International Sustainability Standards Board (priority 95)
- **TCFD**: Task Force on Climate-related Financial Disclosures (priority 90)
- **SASB**: Sustainability Accounting Standards Board (priority 85)
- **CDP**: Carbon Disclosure Project (priority 80)
- **UN_SDG**: UN Sustainable Development Goals (priority 75)
- **ISO14001**: ISO 14001 Environmental Management (priority 70)
- **IFC_PS**: IFC Performance Standards (priority 65)

## Error Handling

All errors returned using RFC 7807 Problem Details format:

### Email Already Exists (409 Conflict)
```json
{
  "type": "https://api.totalesg360.com/problems/conflict",
  "title": "Conflict",
  "status": 409,
  "detail": "Email admin@example.com is already registered",
  "instance": "/api/v1/auth/signup/"
}
```

### Organization Name Taken (409 Conflict)
```json
{
  "type": "https://api.totalesg360.com/problems/conflict",
  "title": "Conflict",
  "status": 409,
  "detail": "Organization name 'Acme Corp' is already taken",
  "instance": "/api/v1/auth/signup/"
}
```

### Invalid Sector (400 Bad Request)
```json
{
  "type": "https://api.totalesg360.com/problems/bad-request",
  "title": "Bad request",
  "status": 400,
  "detail": "Invalid sector 'tech'. Must be one of: manufacturing, oil_gas, finance",
  "instance": "/api/v1/auth/signup/"
}
```

### Invalid Regulatory Coverage (400 Bad Request)
```json
{
  "type": "https://api.totalesg360.com/problems/bad-request",
  "title": "Bad request",
  "status": 400,
  "detail": "Invalid regulatory_coverage 'EU'. Must be one of: NIGERIA, INTERNATIONAL, HYBRID",
  "instance": "/api/v1/auth/signup/"
}
```

## Architecture Principles

### HackSoft Django Style Guide Compliance
✅ Business logic in service layer (`accounts/services/signup.py`)
✅ Views are thin - only validation and response formatting
✅ Serializers only validate input shapes - no business logic
✅ Domain exceptions raised from services
✅ Atomic transactions for data consistency
✅ Structured logging with context

### Extensibility
- **New jurisdictions**: Add new choices to `Organization.RegulatoryCoverage`
- **New frameworks**: Add via Django admin or seed command
- **Sector-specific logic**: Framework assignment already filters by sector
- **Future customization**: `OrganizationFramework.is_enabled` allows per-org overrides

### Auditability
- All framework assignments tracked with timestamps
- `assigned_by` field captures who made manual changes
- System assignments have `assigned_by=None`
- Immutable fields: sector (admin override only)
- Expand-only: regulatory_coverage (can add, not remove jurisdictions)

### Security
- Password minimum 8 characters (enforced by serializer)
- Email uniqueness enforced at DB level
- Organization name uniqueness enforced
- Atomic transactions prevent partial state
- Domain exceptions prevent invalid configurations

## Management Commands

### Seed Frameworks
```bash
python manage.py seed_frameworks
```
Creates/updates 14 regulatory frameworks (6 Nigerian, 8 International)

### Seed Roles (Prerequisite)
```bash
python manage.py seed_roles
```
Creates org_admin role required for signup

## Database Schema

```
accounts_user
├── id (UUID, PK)
├── email (unique)
├── password (hashed)
└── ... (AbstractUser fields)

organizations_organization
├── id (UUID, PK)
├── name (unique)
├── sector (choice)
├── country (CountryField)
├── regulatory_coverage (choice) [NEW]
└── is_active

organizations_regulatory_framework
├── id (UUID, PK)
├── code (unique)
├── name
├── jurisdiction (NIGERIA | INTERNATIONAL)
├── sector (optional)
├── is_active
└── priority

organizations_organization_framework (M2M through)
├── id (UUID, PK)
├── organization_id (FK)
├── framework_id (FK)
├── is_primary
├── is_enabled
├── assigned_at
└── assigned_by (FK, nullable)

organizations_membership
├── id (UUID, PK)
├── user_id (FK)
├── organization_id (FK)
├── role_id (FK)
├── is_active
└── added_by (FK, nullable)
```

## Testing Strategy

### Unit Tests
- `_validate_signup_data`: Email/org name conflicts, invalid sector/coverage
- `_assign_regulatory_frameworks`: Verify correct frameworks assigned per coverage + sector

### Integration Tests
- Full signup flow: user + org + frameworks created atomically
- Rollback behavior on service errors
- Verify framework count matches expected (NIGERIA=6, INTERNATIONAL=8, HYBRID=14 for manufacturing)

### Test Example
```python
def test_signup_hybrid_coverage_manufacturing():
    result = signup(
        email="test@example.com",
        password="testpass123",
        first_name="Test",
        last_name="User",
        organization_name="Test Org",
        sector="manufacturing",
        country="NG",
        regulatory_coverage="HYBRID",
    )
    
    org = Organization.objects.get(id=result["organization_id"])
    frameworks = org.framework_assignments.count()
    
    # Should have: NESREA, FMEnv, NSE_ESG + 8 international = 11 frameworks
    assert frameworks == 11
    assert org.framework_assignments.filter(is_primary=True).count() == 1
```

## Rationale

### Configuration-First Design
Frontend does NOT select individual frameworks. This ensures:
- Consistency across organizations in same sector/jurisdiction
- Admin control over available frameworks
- Easy addition of new frameworks without frontend changes
- Regulatory updates handled server-side

### Sector + Coverage Model
Decouples jurisdiction from framework selection:
- Oil & Gas in Nigeria → gets DPR, NUPRC + cross-sector Nigerian frameworks
- Manufacturing in hybrid mode → gets Nigerian + international frameworks
- Finance in Nigeria → gets CBN_ESG + other Nigerian frameworks

### Expand-Only Coverage
Organizations can broaden scope (NIGERIA → HYBRID) but not reduce:
- Prevents accidental compliance gap
- Admin override available for exceptional cases
- Audit trail preserved

### Primary Framework
First assigned framework marked primary for:
- Default reporting dashboard
- Primary disclosure template
- Prioritized compliance alerts

## Future Enhancements
- EU taxonomy support (new jurisdiction + frameworks)
- US SEC climate disclosure rules
- Industry-specific frameworks (e.g., Equator Principles for finance)
- Framework versioning (e.g., GRI v2021 vs v2024)
- Multi-year compliance tracking
- Framework maturity scoring
