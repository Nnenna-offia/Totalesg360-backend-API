"""
PRACTICAL API EXAMPLES: Creating Indicato → Framework Mapping Workflow

This demonstrates the complete flow from indicator creation through framework mapping.
"""

# ==============================================================================
# EXAMPLE 1: CREATE INDICATOR
# ==============================================================================

POST /api/v1/indicators/
Content-Type: application/json

{
  "code": "Scope1_GHG",
  "name": "Scope 1 GHG Emissions",
  "description": "Direct greenhouse gas emissions from owned/controlled sources",
  "pillar": "ENV",
  "data_type": "number",
  "unit": "tCO2e",
  "collection_method": "activity",  // "activity" or "direct"
  "is_active": true,
  "version": "1.0"
}

RESPONSE (201 Created):
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "code": "Scope1_GHG",
  "name": "Scope 1 GHG Emissions",
  "pillar": "ENV",
  "data_type": "number",
  "unit": "tCO2e",
  "collection_method": "activity"
}


# ==============================================================================
# EXAMPLE 2a: MAP TO ACTIVITY (If collection_method = "activity")
# ==============================================================================

POST /api/v1/activity-types/
Content-Type: application/json

{
  "name": "On-Site Energy Consumption",
  "description": "Direct energy use from on-site renewable/non-renewable sources",
  "indicator": "550e8400-e29b-41d4-a716-446655440000",  // Scope1_GHG
  "scope": "Scope 1",
  "data_type": "number",
  "unit": "kWh",
  "requires_evidence": false,
  "is_required": true,
  "display_order": 1
}

RESPONSE (201 Created):
{
  "id": "660e8400-e29b-41d4-a716-446655440001",
  "name": "On-Site Energy Consumption",
  "indicator": "550e8400-e29b-41d4-a716-446655440000",
  "scope": "Scope 1",
  "data_type": "number",
  "unit": "kWh"
}

# Now employees can submit activities:
POST /api/v1/activities/
{
  "organization": "org-id",
  "activity_type": "660e8400-e29b-41d4-a716-446655440001",
  "reporting_period": "period-id",
  "value": 5000,  // 5000 kWh
  "evidence": "file-upload-url"
}


# ==============================================================================
# EXAMPLE 2b: CREATE FRAMEWORK REQUIREMENTS (NEW - Layer 2b)
# ==============================================================================

# Step 1: Define requirements for each framework

POST /api/v1/compliance/framework-requirements/
{
  "framework": "gri-framework-id",
  "code": "GRI 305-1",
  "title": "Direct (Scope 1) GHG Emissions",
  "description": "Report direct GHG emissions from operations under organizational control",
  "pillar": "environmental",
  "is_mandatory": true,
  "status": "active",
  "priority": 1,
  "guidance_url": "https://www.globalreporting.org/...",
  "version": "GRI 2024"
}

RESPONSE (201 Created):
{
  "id": "77e8400-e29b-41d4-a716-446655440002",
  "framework": "gri-framework-id",
  "code": "GRI 305-1",
  "title": "Direct (Scope 1) GHG Emissions",
  "pillar": "environmental",
  "is_mandatory": true
}

# Create for IFRS
POST /api/v1/compliance/framework-requirements/
{
  "framework": "ifrs-framework-id",
  "code": "IFRS S2-1",
  "title": "Governance Structure and Management Processes",
  "description": "Disclose governance structure related to physical and transition risks",
  "pillar": "environmental",
  "is_mandatory": true,
  "status": "active",
  "priority": 1,
  "guidance_url": "https://www.ifrs.org/...",
  "version": "IFRS 2024"
}

RESPONSE (201 Created):
{
  "id": "88e8400-e29b-41d4-a716-446655440003",
  "framework": "ifrs-framework-id",
  "code": "IFRS S2-1",
  "title": "Governance Structure and Management Processes",
  "pillar": "environmental"
}


# ==============================================================================
# EXAMPLE 3: MAP INDICATOR TO FRAMEWORK REQUIREMENTS (NEW - Layer 2b)
# ==============================================================================

# Map Scope1_GHG to GRI 305-1
POST /api/v1/compliance/indicator-mappings/
{
  "indicator": "550e8400-e29b-41d4-a716-446655440000",  // Scope1_GHG
  "framework": "gri-framework-id",
  "requirement": "77e8400-e29b-41d4-a716-446655440002",  // GRI 305-1
  "mapping_type": "primary",      // primary/supporting/reference
  "is_primary": true,
  "coverage_percent": 100,
  "rationale": "This indicator directly reports Scope 1 emissions as required by GRI 305-1",
  "notes": "Includes emissions from energy generation, manufacturing, transportation",
  "is_active": true
}

RESPONSE (201 Created):
{
  "id": "99e8400-e29b-41d4-a716-446655440004",
  "indicator": "550e8400-e29b-41d4-a716-446655440000",
  "framework": "gri-framework-id",
  "requirement": "77e8400-e29b-41d4-a716-446655440002",
  "mapping_type": "primary",
  "is_primary": true,
  "coverage_percent": 100,
  "created_at": "2026-04-12T10:30:00Z"
}

# Map same indicator to IFRS S2-1
POST /api/v1/compliance/indicator-mappings/
{
  "indicator": "550e8400-e29b-41d4-a716-446655440000",  // Scope1_GHG
  "framework": "ifrs-framework-id",
  "requirement": "88e8400-e29b-41d4-a716-446655440003",  // IFRS S2-1
  "mapping_type": "primary",
  "is_primary": true,
  "coverage_percent": 100,
  "rationale": "Demonstrates governance of climate risks through emissions data",
  "is_active": true
}

RESPONSE (201 Created):
{
  "id": "aae8400-e29b-41d4-a716-446655440005",
  ...
}


# ==============================================================================
# EXAMPLE 4: QUERY - Get All Frameworks for an Indicator
# ==============================================================================

GET /api/v1/compliance/indicator-mappings/for_indicator/?indicator_id=550e8400-e29b-41d4-a716-446655440000

RESPONSE (200 OK):
{
  "indicator": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "code": "Scope1_GHG",
    "name": "Scope 1 GHG Emissions"
  },
  "frameworks": [
    {
      "framework": {
        "id": "gri-framework-id",
        "code": "GRI",
        "name": "Global Reporting Initiative"
      },
      "requirements": [
        {
          "code": "GRI 305-1",
          "title": "Direct (Scope 1) GHG Emissions",
          "mapping_type": "primary",
          "coverage_status": "full",
          "is_primary": true,
          "coverage_percent": 100
        }
      ]
    },
    {
      "framework": {
        "id": "ifrs-framework-id",
        "code": "IFRS",
        "name": "International Sustainability Standards Board"
      },
      "requirements": [
        {
          "code": "IFRS S2-1",
          "title": "Governance Structure and Management Processes",
          "mapping_type": "primary",
          "coverage_status": "full",
          "is_primary": true,
          "coverage_percent": 100
        }
      ]
    }
  ],
  "total_frameworks": 2
}


# ==============================================================================
# EXAMPLE 5: GAP ANALYSIS - Find Uncovered Requirements
# ==============================================================================

GET /api/v1/compliance/indicator-mappings/gaps/?organization_id=org-id&framework_id=gri-framework-id

RESPONSE (200 OK):
{
  "organization": {
    "id": "org-id",
    "name": "Total ESG Company"
  },
  "framework": {
    "id": "gri-framework-id",
    "code": "GRI",
    "name": "Global Reporting Initiative"
  },
  "gaps": {
    "environmental": [
      {
        "id": "gap-1",
        "code": "GRI 305-3",
        "title": "Indirect (Scope 3) GHG Emissions",
        "description": "Report indirect GHG emissions from value chain",
        "is_mandatory": true,
        "status": "active",
        "priority": 1
      },
      {
        "id": "gap-2",
        "code": "GRI 305-5",
        "title": "Reduction of GHG Emissions",
        "description": "Report efforts and results reducing GHG emissions",
        "is_mandatory": true,
        "status": "active",
        "priority": 2
      }
    ],
    "social": [],
    "governance": [
      {
        "id": "gap-3",
        "code": "GRI 404-1",
        "title": "Average Hours of Training",
        "description": "Report training and education programs",
        "is_mandatory": true,
        "status": "active"
      }
    ]
  },
  "total_gaps": 3
}


# ==============================================================================
# EXAMPLE 6: ORGANIZATION FRAMEWORK COVERAGE
# ==============================================================================

GET /api/v1/compliance/organization-frameworks/status/
X-ORG-ID: org-id

RESPONSE (200 OK):
[
  {
    "organization_framework": {
      "id": "org-fw-1",
      "is_primary": true,
      "is_enabled": true,
      "assigned_at": "2025-01-15T09:00:00Z"
    },
    "framework": {
      "id": "gri-framework-id",
      "code": "GRI",
      "name": "Global Reporting Initiative"
    },
    "total_requirements": 45,
    "covered_requirements": 38,
    "uncovered_requirements": 7,
    "coverage_percent": 84.4,
    "by_pillar": {
      "environmental": {
        "total": 15,
        "covered": 12,
        "uncovered": 3,
        "coverage_percent": 80.0
      },
      "social": {
        "total": 18,
        "covered": 16,
        "uncovered": 2,
        "coverage_percent": 88.9
      },
      "governance": {
        "total": 12,
        "covered": 10,
        "uncovered": 2,
        "coverage_percent": 83.3
      }
    },
    "is_primary": true
  },
  {
    "organization_framework": {
      "id": "org-fw-2",
      "is_primary": false,
      "is_enabled": true,
      "assigned_at": "2025-02-20T14:30:00Z"
    },
    "framework": {
      "id": "ifrs-framework-id",
      "code": "IFRS",
      "name": "International Sustainability Standards Board"
    },
    "total_requirements": 28,
    "covered_requirements": 24,
    "uncovered_requirements": 4,
    "coverage_percent": 85.7,
    "by_pillar": {
      "environmental": {
        "total": 12,
        "covered": 10,
        "uncovered": 2,
        "coverage_percent": 83.3
      },
      "social": {
        "total": 10,
        "covered": 9,
        "uncovered": 1,
        "coverage_percent": 90.0
      },
      "governance": {
        "total": 6,
        "covered": 5,
        "uncovered": 1,
        "coverage_percent": 83.3
      }
    },
    "is_primary": false
  }
]


# ==============================================================================
# SUMMARY OF FLOWS
# ==============================================================================

COMPLETE DATA FLOW:

1. CREATE INDICATOR
   └─ Defines what to track (e.g., Scope1_GHG)

2. MAP TO ACTIVITY (if collection_method="activity")
   └─ Defines how to collect data (e.g., On-Site Energy Use)
   └─ Employees submit activities daily
   └─ Aggregated to indicator scores

3. MAP TO FRAMEWORKS
   └─ Defines compliance requirements (e.g., GRI 305-1, IFRS S2-1)
   └─ Tracks how indicators satisfy requirements
   └─ Enables gap analysis
   └─ Generates compliance reports

4. QUERY & ANALYZE
   └─ Find frameworks for indicators
   └─ Find indicators for frameworks
   └─ Identify coverage gaps
   └─ Generate compliance status reports


API ENDPOINTS SUMMARY:

POST   /api/v1/indicators/                           - Create indicator
POST   /api/v1/activity-types/                       - Map to activity
POST   /api/v1/compliance/framework-requirements/    - Define requirement
POST   /api/v1/compliance/indicator-mappings/        - Map indicator to requirement

GET    /api/v1/compliance/indicator-mappings/for_indicator/    - Get frameworks
GET    /api/v1/compliance/indicator-mappings/for_framework/    - Get indicators
GET    /api/v1/compliance/indicator-mappings/gaps/             - Find gaps
GET    /api/v1/compliance/organization-frameworks/status/      - Compliance dashboard
