# TotalESG360 - Complete System Architecture Guide
## From Onboarding to Reporting & Disclosure (Layer 8)

**Last Updated:** April 14, 2026  
**System Version:** Layer 8 Complete  
**Status:** Production Ready

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Onboarding Flow](#onboarding-flow)
3. [System Architecture Layers](#system-architecture-layers)
   - [Layer 1: Enterprise Hierarchy](#layer-1-enterprise-hierarchy)
   - [Layer 2: Regulatory Framework Mapping](#layer-2-regulatory-framework-mapping)
   - [Layer 3: Data Collection & Indicators](#layer-3-data-collection--indicators)
   - [Layer 4: Activity-Based Reporting](#layer-4-activity-based-reporting)
   - [Layer 5: Compliance & Intelligence](#layer-5-compliance--intelligence)
   - [Layer 6: ESG Scoring](#layer-6-esg-scoring)
   - [Layer 7: Group Consolidation & Analytics](#layer-7-group-consolidation--analytics)
   - [Layer 8: Reporting & Disclosure Engine](#layer-8-reporting--disclosure-engine)
4. [Data Flow Architecture](#data-flow-architecture)
5. [Key Models & Relationships](#key-models--relationships)
6. [API Endpoints by Layer](#api-endpoints-by-layer)
7. [Authentication & Authorization](#authentication--authorization)
8. [Error Handling Pattern](#error-handling-pattern)

---

## System Overview

**TotalESG360** is a comprehensive Environmental, Social, and Governance (ESG) compliance and reporting platform designed for multi-tenant, multi-hierarchy organizations.

### Core Capabilities

- **Enterprise-Grade Hierarchy Support**: Groups, subsidiaries, facilities, departments
- **Multi-Framework Compliance**: GRI, ISSB, TCFD, NESREA, CBN, and more
- **Automated Data Aggregation**: Real-time ESG scoring and compliance gap identification
- **Smart Reporting**: Multi-format reports for stakeholders (JSON, CSV, HTML, PDF)
- **Regulatory Intelligence**: Framework-specific compliance tracking and recommendations
- **Group Consolidation**: Subsidiary-level analytics rolled up to group level

### Architecture Principles

1. **Layered Design**: Each layer builds on previous layers, no circular dependencies
2. **Signal-Driven Updates**: Changes cascade automatically (e.g., new indicator → regenerate ESG score)
3. **Selector Pattern**: Read operations use explicit selector functions for maintainability
4. **RFC7807 Error Handling**: Standardized problem response format across all APIs
5. **Audit Trail**: Creation and modification timestamps on all entities

---

## Onboarding Flow

### Phase 1: User Registration & Authentication

```
1. User signs up with email/password
   → POST /api/v1/accounts/register/
   → Credentials validated, user created
   → Email verification sent

2. User verifies email
   → Click verification link
   → Email marked as verified

3. User logs in
   → POST /api/v1/accounts/login/
   → JWT tokens issued (access + refresh)
   → User can now access dashboard
```

### Phase 2: Organization Setup

**Step 1: Create Root Organization**

```
POST /api/v1/organizations/
{
  "name": "Acme Corporation",
  "sector": "manufacturing",
  "country": "NG",
  "primary_reporting_focus": "NIGERIA",
  "organization_type": "group",
  "registered_name": "Acme Corp Ltd",
  "company_size": "large"
}

Response:
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Acme Corporation",
  "organization_type": "group"
}
```

**Step 2: Configure Regulatory Frameworks**

```
GET /api/v1/organizations/{org_id}/framework-options/
→ Returns list of available frameworks (GRI, ISSB, NESREA, etc.)

POST /api/v1/organizations/{org_id}/frameworks/assign/
{
  "framework_id": "gri-uuid",
  "is_primary": true
}
→ Framework assigned to organization
```

**Step 3: Create Hierarchy (Optional)**

```
POST /api/v1/organizations/
{
  "parent_id": "acme-group-uuid",
  "name": "Acme Lagos facility",
  "organization_type": "facility",
  "sector": "manufacturing",
  "country": "NG"
}
→ Facility created under Acme Group
```

### Phase 3: Data Infrastructure Setup

**Step 1: Define Indicators**

```
GET /api/v1/indicators/?framework=GRI
→ Returns all GRI indicators (Scope 1, 2, 3 emissions, Labor practices, etc.)

POST /api/v1/organizations/{org_id}/indicator-config/
[
  {"indicator_id": "gri-305-1", "is_required": true},
  {"indicator_id": "gri-305-2", "is_required": true},
  {"indicator_id": "gri-408-1", "is_required": false}
]
→ Organization's indicator configuration saved
```

**Step 2: Configure Collection Methods**

```
POST /api/v1/indicators/{indicator_id}/collection-method/
{
  "method": "manual",
  "frequency": "quarterly",
  "responsible_department": "Finance"
}
→ Collection workflow defined
```

---

## System Architecture Layers

### Layer 1: Enterprise Hierarchy

**Purpose**: Manage multi-level organization structures with inheritance and rollup capabilities.

**Key Models**:
- `Organization`: Groups, subsidiaries, facilities, departments
- `OrganizationFramework`: Maps frameworks to organizations
- `BusinessUnit`: Department/cost center management

**Data Structure**:

```
Organization (Hierarchy)
├── id (UUID)
├── parent (ForeignKey to Organization)
├── organization_type: GROUP | SUBSIDIARY | FACILITY | DEPARTMENT
├── name
├── sector
├── country
└── framework_assignments (M2M through OrganizationFramework)
```

**Key Operations**:

```python
# Get all subsidiaries of a group
subsidiaries = org.subsidiaries.all()

# Get hierarchical path
path = org.get_hierarchy_path()  # e.g., "Acme Group > Lagos Facility"

# Get root organization
root = org.get_root()
```

**API Endpoints**:

```
POST   /api/v1/organizations/                    # Create org
GET    /api/v1/organizations/                    # List orgs
GET    /api/v1/organizations/{id}/               # Get org details
PATCH  /api/v1/organizations/{id}/               # Update org
GET    /api/v1/organizations/{id}/hierarchy/     # Get org tree
POST   /api/v1/organizations/{id}/frameworks/    # Assign framework
```

---

### Layer 2: Regulatory Framework Mapping

**Purpose**: Define ESG frameworks and their requirements, linking organizations to compliance obligations.

**Key Models**:
- `RegulatoryFramework`: Framework definitions (GRI, ISSB, NESREA, etc.)
- `FrameworkRequirement`: Individual requirements within frameworks
- `FrameworkIndicator`: Links requirements to data indicators
- `OrganizationFramework`: Organization's relationship with frameworks

**Framework Structure**:

```
RegulatoryFramework (e.g., "GRI")
├── code: "GRI"
├── jurisdiction: NIGERIA | INTERNATIONAL
├── priority: 100
└── requirements (M2M)
    ├── GRI 305-1: Direct GHG Emissions (Required)
    ├── GRI 305-2: Energy Indirect GHG (Required)
    ├── GRI 408-1: Child Labor Assessment (Optional)
    └── ... (many more)
```

**Requirement Fields**:

```python
FrameworkRequirement:
  - code: "GRI 305-1"
  - title: "Direct GHG Emissions"
  - description: "Report Scope 1 greenhouse gas emissions"
  - pillar: ENV | SOC | GOV
  - is_mandatory: True
  - status: ACTIVE | DEPRECATED | ARCHIVED
```

**Key Operations**:

```python
# Get all requirements for a framework
requirements = framework.requirements.all()

# Get mandatory requirements only
mandatory = framework.requirements.filter(is_mandatory=True)

# Check organization's coverage
coverage = org.get_framework_coverage(framework)  # e.g., 62%
```

**API Endpoints**:

```
GET    /api/v1/frameworks/                       # List frameworks
GET    /api/v1/frameworks/{id}/requirements/     # Get requirements
GET    /api/v1/organizations/{id}/framework-readiness/  # Coverage %
```

---

### Layer 3: Data Collection & Indicators

**Purpose**: Define what data is collected, how it's collected, and organize it for reporting.

**Key Models**:
- `Indicator`: Definition of an ESG metric (e.g., "Scope 1 Emissions")
- `IndicatorValue`: Actual data point for an indicator in a period
- `FrameworkIndicator`: Maps indicators to framework requirements
- `OrganizationIndicator`: Organization's configuration of indicators

**Indicator Hierarchy**:

```
Indicator (e.g., "Scope 1 GHG Emissions")
├── code: "ENV-EMISSIONS-S1"
├── name: "Scope 1 Greenhouse Gas Emissions"
├── pillar: ENV | SOC | GOV
├── data_type: NUMBER | PERCENT | CURRENCY | TEXT
├── unit: "tCO2e"
├── collection_method: MANUAL | SYSTEM | DERIVED
└── framework_mappings (M2M)
    ├── GRI 305-1
    ├── ISSB S2-1A.1
    └── TCFD Emissions

IndicatorValue (actual data)
├── indicator (FK)
├── organization (FK)
├── reporting_period (FK)
├── value: 1250.50
├── unit_override: "tCO2e"
└── notes: "2025 Q1 scope 1 emissions"
```

**Collection Workflow**:

```
1. Define indicator needs
   → GET /api/v1/indicators/?framework=GRI

2. Configure for organization
   → POST /api/v1/organizations/{id}/indicator-config/
   → Set: required, active, collection frequency

3. Submit data
   → POST /api/v1/indicator-values/
   {
     "indicator_id": "scope1-uuid",
     "reporting_period_id": "q1-2026-uuid",
     "value": 1250.50,
     "notes": "From facility reports"
   }

4. System triggers
   → Validates against framework requirements
   → Calculates coverage %
   → Updates readiness score
   → Regenerates ESG score
```

**API Endpoints**:

```
GET    /api/v1/indicators/                       # List indicators
GET    /api/v1/indicators/{id}/details/          # Get indicator metadata
POST   /api/v1/indicator-values/                 # Submit data point
GET    /api/v1/indicator-values/?period=2026-Q1  # Get submitted values
PATCH  /api/v1/indicator-values/{id}/            # Update data point
```

---

### Layer 4: Activity-Based Reporting

**Purpose**: Track ESG-related activities and initiatives, linking them to indicators.

**Key Models**:
- `ActivityType`: Types of ESG activities (e.g., "GHG Reduction Project")
- `Activity`: Specific activities/initiatives
- `ActivitySubmission`: Submission of activity data in a reporting period

**Activity Flow**:

```
ActivityType (e.g., "Renewable Energy Installation")
├── code: "RENEWABLE-INSTALL"
├── name: "Renewable Energy Installation"
├── description: "Installation of solar/wind capacity"
├── pillar: ENV
├── indicators (M2M)

Activity (actual project)
├── organization: "Acme Lagos"
├── activity_type: "Renewable Energy Installation"
├── name: "Lagos Solar Farm - Phase 1"
├── start_date: "2025-01-15"
├── target_completion: "2026-06-30"
├── description: "500kW solar capacity"
├── status: IN_PROGRESS | COMPLETED | DEFERRED

ActivitySubmission (reporting)
├── activity: (FK)
├── reporting_period: "2026 Q1"
├── kwh_generated: 125000
├── impact_units: 150  # tCO2e reduced
└── notes: "On track for Q2 completion"
```

**Signal Cascade**:

```
User creates Activity
  ↓
Activity.post_save signal fires
  ↓
Trigger indicator value calculation
  ↓
Update coverage %
  ↓
Recalculate ESG score
  ↓
Update framework readiness
  ↓
Signal all reports to regenerate
```

**API Endpoints**:

```
GET    /api/v1/activity-types/                   # List activity templates
POST   /api/v1/activities/                       # Create activity initiative
GET    /api/v1/activities/?org={id}              # List org's activities
POST   /api/v1/activity-submissions/             # Submit activity data
GET    /api/v1/organizations/{id}/activity-impact/  # Aggregate impact
```

---

### Layer 5: Compliance & Intelligence

**Purpose**: Track framework compliance, identify gaps, and provide remediation recommendations.

**Key Models**:
- `FrameworkReadiness`: Overall compliance status for each org-framework pair
- `ComplianceGapPriority`: Ranked list of compliance gaps
- `ComplianceRecommendation`: AI-generated remediation recommendations

**Framework Readiness**:

```
FrameworkReadiness
├── organization (FK)
├── framework (FK)
├── reporting_period (FK)
├── total_requirements: 100
├── covered_requirements: 62          # Has data/met requirement
├── coverage_percent: 62.0%
├── mandatory_requirements: 50
├── mandatory_covered: 40
├── mandatory_coverage_percent: 80.0%
├── readiness_score: 74.0            # Weighted score
├── risk_level: HIGH | MEDIUM | LOW
├── last_assessed_at: timestamp
```

**Compliance Gap Priority**:

```
ComplianceGapPriority (weighted gap ranking)
├── organization (FK)
├── framework (FK)
├── requirement (FK: GRI 305-1)
├── priority_score: 0-100            # Calculated from:
│   ├── mandatory_weight: 40%
│   ├── framework_weight: 30%
│   ├── pillar_weight: 20%
│   └── coverage_impact_weight: 10%
├── priority_level: HIGH | MEDIUM | LOW
├── gap_description: "No Scope 1 data collected"
├── efforts_to_close: "Implement emissions tracking"
├── estimated_effort_days: 45
├── is_active: True
```

**Recommendation Engine**:

```
ComplianceRecommendation
├── organization (FK)
├── framework (FK)
├── requirement (FK)
├── recommendation_type:
│   - CREATE_INDICATOR
│   - ENHANCE_DATA
│   - INTEGRATE_SYSTEM
│   - IMPLEMENT_PROCESS
│   - TRAINING_REQUIRED
├── title: "Implement Scope 1 emissions monitoring"
├── description: "Set up system to track fuel consumption..."
├── actionable_steps: [
│     "Step 1: Identify all emission sources",
│     "Step 2: Purchase monitoring equipment",
│     "Step 3: Train staff"
│   ]
├── priority: HIGH | MEDIUM | LOW
├── impact_score: 8.5 (out of 10)
├── estimated_effort_days: 45
├── status: PENDING | IN_PROGRESS | COMPLETED
```

**Gap Analysis Workflow**:

```
1. Calculate current coverage
   → indicators_submitted / total_requirements

2. Identify uncovered requirements
   → requirements without indicator_values

3. Rank gaps by priority
   → ComplianceGapPriority with weighted calculation

4. Generate recommendations
   → AI-driven suggestions based on gap type

5. Track remediation
   → Update status as actions completed

6. Regenerate readiness
   → Recalculate coverage % and risk level
```

**API Endpoints**:

```
GET    /api/v1/organizations/{id}/framework-readiness/  # Coverage overview
GET    /api/v1/organizations/{id}/compliance-gaps/      # Gap list
GET    /api/v1/organizations/{id}/gap-analysis/         # Detailed analysis
GET    /api/v1/organizations/{id}/recommendations/      # Action items
POST   /api/v1/recommendations/{id}/mark-completed/     # Track progress
```

---

### Layer 6: ESG Scoring

**Purpose**: Calculate organization-level Environmental, Social, and Governance scores based on performance.

**Key Models**:
- `ESGScore`: Overall ESG performance scoring
- `PillarScore`: Pillar-specific scores (ENV, SOC, GOV)

**Scoring Methodology**:

```
ESGScore (per organization, per reporting period)
├── organization (FK)
├── reporting_period (FK)
├── environmental_score: 0-100      # E pillar
│   ← Average of ENV indicator performance
├── social_score: 0-100             # S pillar
│   ← Average of SOC indicator performance
├── governance_score: 0-100         # G pillar
│   ← Average of GOV indicator performance
├── overall_score: 0-100
│   ← (E + S + G) / 3
├── calculation_date: timestamp
```

**Score Calculation Algorithm**:

```python
# For each pillar:
1. Get all indicators for pillar that org is required to report
2. For each indicator:
   - Get latest submitted value
   - Compare against benchmark/target
   - Calculate score (0-100)
   - Weight by importance
3. Average all indicator scores
4. Apply pillar weight

# Overall score = (ENV_score × 0.35 + SOC_score × 0.35 + GOV_score × 0.30)

# Rating mapping:
80-100: EXCELLENT
60-79:  GOOD
40-59:  MODERATE
20-39:  WEAK
0-19:   CRITICAL
```

**Score Triggers**:

```
Signal: IndicatorValue.post_save
  ↓ Calculate pillar average
  ↓ Calculate overall score
  ↓ Create/Update ESGScore
  ↓ Trigger Layer 7 & 8 recalculation
```

**API Endpoints**:

```
GET    /api/v1/organizations/{id}/esg-score/            # Latest score
GET    /api/v1/organizations/{id}/esg-score/history/    # Scores over time
GET    /api/v1/organizations/{id}/esg-score/compare/    # vs benchmarks
GET    /api/v1/organizations/{id}/pillar-breakdown/     # E/S/G detail
```

---

### Layer 7: Group Consolidation & Analytics

**Purpose**: Aggregate subsidiary-level data to group level with sophisticated rollup logic.

**Key Models**:
- `GroupDashboard`: Group-level aggregation
- Selectors for hierarchy traversal

**Group-Level Analytics**:

```
get_group_dashboard(group_org, reporting_period)
  ↓ Returns:
  {
    "organization": "Acme Group",
    "subsidiaries_count": 5,
    "total_facilities": 12,
    "overall_esg": {
      "score": 58.5,
      "rating": "MODERATE",
      "environmental": 62.0,
      "social": 55.0,
      "governance": 58.0
    },
    "subsidiary_scores": [
      {"name": "Acme Lagos", "score": 72.0, "rating": "GOOD"},
      {"name": "Acme Abuja", "score": 45.0, "rating": "MODERATE"},
      ...
    ],
    "aggregate_readiness": {
      "frameworks": 3,
      "avg_coverage": 58.0,
      "high_risk_frameworks": 1,
      "medium_risk_frameworks": 1
    }
  }
```

**Consolidation Logic**:

```python
# Method: Weighted Average (by facility count or revenue)

def calculate_group_esg_score(group, period):
    subsidiaries = group.subsidiaries.all()
    
    scores = []
    weights = []
    
    for subsidiary in subsidiaries:
        esg = ESGScore.objects.get(
            organization=subsidiary,
            reporting_period=period
        )
        scores.append(esg.overall_score)
        weights.append(subsidiary.weight)  # Based on size, revenue, etc.
    
    group_score = sum(s * w for s, w in zip(scores, weights)) / sum(weights)
    return group_score
```

**Rollup Cascade**:

```
Subsidiary 1 ESG Score changes (58.5)
  ↓
Trigger get_group_dashboard(parent_group)
  ↓
Recalculate group average
  ↓
Update parent group score (65.2)
  ↓
Trigger parent's parent (if exists)
  ↓
Cascade up entire hierarchy
```

**API Endpoints**:

```
GET    /api/v1/organizations/{id}/group-dashboard/      # Dashboard
GET    /api/v1/organizations/{id}/subsidiary-ranking/   # Subsidiary performance
GET    /api/v1/organizations/{id}/hierarchy-analytics/  # Full tree view
GET    /api/v1/organizations/{id}/consolidation-report/ # Rollup details
```

---

### Layer 8: Reporting & Disclosure Engine

**Purpose**: Generate multi-format ESG reports for stakeholders, aggregating data from all previous layers.

**Key Models**:
- `Report`: Report metadata and status
- Selectors for report-specific aggregation
- Export service for multi-format output

**Report Types**:

```
1. ESG Summary Report
   ├── Overall ESG scores (E/S/G)
   ├── Framework readiness summary
   ├── Top 5 compliance gaps
   ├── Top 5 remediation recommendations
   └── Overall rating and key insights

2. Framework-Specific Report
   ├── Framework code & name
   ├── Coverage % for this framework
   ├── Risk assessment
   ├── Framework-specific gaps
   ├── Remediation roadmap
   └── Compliance status

3. Group Consolidation Report
   ├── Group overall score
   ├── Subsidiary performance ranking
   ├── Consolidated gaps
   ├── Rollup methodology
   └── Consolidated recommendations

4. Compliance Gap Report
   ├── Gaps ranked by priority
   ├── Gap-by-priority distribution
   ├── Gap-by-status summary
   ├── Critical gaps detail
   ├── Remediation recommendations
   └── Resolution timeline

5. Partner-Specific Reports (DEG, USAID, GCF, FRC)
   ├── Partner-customized format
   ├── Partner-relevant metrics
   ├── Partner-specific recommendations
   └── Partner compliance status
```

**Report Model**:

```
Report
├── id (UUID)
├── organization (FK)
├── report_type: ESG_SUMMARY | FRAMEWORK | GROUP | GAP | PARTNER
├── framework (FK, optional - for FRAMEWORK type)
├── partner_type: DEG | USAID | GCF | FRC | NONE
├── reporting_period (FK, optional)
├── status: PENDING | GENERATING | COMPLETED | FAILED
├── generated_by (FK to User)
├── file_format: JSON | CSV | HTML | PDF
├── file_url: "s3://bucket/report-uuid.pdf"
├── summary: JSONField         # Quick-access summary
├── metadata: JSONField        # Report parameters
├── generated_at: timestamp
├── expires_at: timestamp      # 1 hour TTL default
```

**Report Generation Flow**:

```
1. User requests report
   POST /api/v1/reports/generate/
   {
     "report_type": "ESG_SUMMARY",
     "file_format": "pdf"
   }

2. Create Report record (status=PENDING)
   ↓

3. Select appropriate selector
   ↓ get_esg_summary_report(org, period)
   ↓ get_framework_report(org, framework)
   ↓ get_group_esg_report(org, period)
   ↓ get_gap_report(org)
   ↓ get_partner_report(org, partner_type)

4. Each selector aggregates from previous layers:
   - Selector calls all dependent selectors
   - Combines results
   - Returns aggregated data

5. Store report data
   report.summary = extracted_summary
   report.metadata = report_params
   report.status = COMPLETED

6. Export to requested format
   export_to_pdf(report_data)
   export_to_csv(report_data)
   export_to_json(report_data)
   export_to_html(report_data)

7. Return to user
   → Download link (for PDF/CSV)
   → JSON response (for JSON/API)
```

**Selector Dependencies**:

```
ESG Summary Selector
├── Calls: ESGScore selector
├── Calls: FrameworkReadiness selector
├── Calls: ComplianceGapPriority selector
├── Calls: ComplianceRecommendation selector
└── Returns: Combined ESG summary

Framework Selector
├── Calls: FrameworkReadiness for specific framework
├── Calls: ComplianceGapPriority filtered by framework
├── Calls: ComplianceRecommendation for framework gaps
└── Returns: Framework-specific report

Group Selector
├── Calls: Group dashboard selector (Layer 7)
├── Calls: Subsidiary ranking selector (Layer 7)
├── Calls: Group ESG score selector (Layer 7)
└── Returns: Group consolidation view

Gap Selector
├── Calls: ComplianceGapPriority selector
├── Aggregates by priority level (HIGH/MEDIUM/LOW)
├── Aggregates by status (ACTIVE/INACTIVE)
└── Returns: Gap-focused report

Partner Selector
├── Calls: ESG Summary selector
├── Re-formats result for partner
├── Filters/highlights relevant sections
└── Returns: Partner-specific view
```

**Multi-Format Export**:

```
JSON Export
├── Full report structure as JSON
├── Easy for API consumption
└── For system integration

CSV Export
├── Tabular format
├── Summary metrics as columns
├── Gap details as rows
└── For spreadsheet analysis

HTML Export
├── Formatted HTML report
├── Styled with company branding
├── Embedded charts/visualizations
└── For email/portal viewing

PDF Export
├── Professional PDF document
├── Multi-page layout
├── Graphs and formatting
└── For printing/archiving
```

**Caching & TTL**:

```
report.expires_at = now() + 1 hour

When report accessed:
  if expires_at > now():
    return cached_report
  else:
    regenerate_report()
    reset expires_at

Signal-driven regeneration:
  ESGScore.post_save → regenerate_all_reports()
  FrameworkReadiness.post_save → regenerate_all_reports()
  ComplianceGapPriority.post_save/delete → regenerate_all_reports()
  ComplianceRecommendation.post_save/delete → regenerate_all_reports()
```

**API Endpoints**:

```
GET    /api/v1/reports/                          # List reports
POST   /api/v1/reports/generate/                 # Generate new report
GET    /api/v1/reports/{id}/                     # Get report details
GET    /api/v1/reports/{id}/download/            # Download (format param)
GET    /api/v1/reports/esg-summary/              # Quick ESG summary
GET    /api/v1/reports/gaps/                     # Quick gap report
GET    /api/v1/reports/group/                    # Quick group report
```

---

## Data Flow Architecture

### Complete Data Journey

```
┌─────────────────────────────────────────────────────────────────┐
│                    USER ONBOARDING                              │
│                                                                 │
│  1. Create Account (Layer 0 - Authentication)                  │
│  2. Create Organization (Layer 1)                              │
│  3. Assign Frameworks (Layer 2)                                │
│  4. Configure Indicators (Layer 3)                             │
│  5. Define Activities (Layer 4)                                │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    DATA SUBMISSION FLOW                         │
│                                                                 │
│  User provides indicator values                                │
│  → POST /api/v1/indicator-values/                             │
│  → Validates against requirements                             │
│  → Stores IndicatorValue record                               │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    LAYER 5: COMPLIANCE CALCULATION              │
│                                                                 │
│  Signal: IndicatorValue.post_save                             │
│    ① Recalculate FrameworkReadiness                           │
│       - Count covered_requirements                            │
│       - Calculate coverage_percent                            │
│    ② Identify ComplianceGapPriority                           │
│       - Find uncovered requirements                           │
│       - Calculate priority scores                             │
│    ③ Generate ComplianceRecommendation                        │
│       - Suggest remediation actions                           │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    LAYER 6: ESG SCORING                         │
│                                                                 │
│  Signal: FrameworkReadiness updated                            │
│    ① Calculate pillar scores (ENV, SOC, GOV)                  │
│    ② Calculate overall score                                   │
│    ③ Map to rating (EXCELLENT/GOOD/MODERATE/WEAK/CRITICAL)   │
│    ④ Store ESGScore record                                     │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    LAYER 7: GROUP CONSOLIDATION                 │
│                                                                 │
│  Signal: ESGScore updated (for subsidiary)                     │
│    ① For each parent in hierarchy:                            │
│       - Get all subsidiary scores                              │
│       - Calculate weighted average                            │
│       - Update parent ESGScore                                │
│    ② Cascade up entire hierarchy                              │
│    ③ Recalculate group dashboards                             │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    LAYER 8: REPORTING                           │
│                                                                 │
│  Signal: Multiple updates (scores, gaps, etc.)                │
│    ① Mark all organization reports as expired                 │
│    ② Reset report generation on next access                   │
│    ③ When user requests report:                              │
│       - Call appropriate selector                             │
│       - Aggregate from Layers 1-7                            │
│       - Format per report type                                │
│       - Export to requested format                            │
│       - Cache with 1-hour TTL                                 │
│       - Return to user                                        │
└─────────────────────────────────────────────────────────────────┘
                              ↓
                    ┌─────────────────────┐
                    │ REPORTING OUTPUT    │
                    │ (ESG Summary)       │
                    │ (Framework Report)  │
                    │ (Gap Report)        │
                    │ (Group Report)      │
                    │ (Partner Report)    │
                    │ (JSON/CSV/HTML/PDF) │
                    └─────────────────────┘
```

### Signal Cascade Example: Single Indicator Update

```
Scenario: User submits "Scope 1 Emissions: 1250.50 tCO2e"

1. POST /api/v1/indicator-values/
   {
     "indicator_id": "gri-305-1",
     "organization_id": "org-uuid",
     "reporting_period_id": "2026-q1",
     "value": 1250.50
   }
   → IndicatorValue created

2. Signal: IndicatorValue.post_save fires
   ↓

3. Layer 5: Compliance Recalculation
   ① FrameworkReadiness for org-GRI:
      - covered_requirements: 62 → 63
      - coverage_percent: 62% → 63%
      - readiness_score: 74.0 → 75.2
      → Signal: FrameworkReadiness.post_save fires
   
   ② ComplianceGapPriority:
      - Check if GRI 305-1 now covered
      - If covered, mark is_active=False (gap resolved)
      → Signal: ComplianceGapPriority modified
   
   ③ ComplianceRecommendation:
      - Check if related recommendations now moot
      - Update status if needed
      → Signal: ComplianceRecommendation modified

4. Layer 6: ESG Score Recalculation
   Signal from FrameworkReadiness.post_save triggers:
   ① ENV pillar average recalculated
      - (Scope 1 + Scope 2 + Scope 3 + ...) / count
      - 62% → 64%
   
   ② ESGScore updated:
      - environmental: 62.0 → 64.2
      - overall: 58.5 → 60.1
      - rating: MODERATE (unchanged)
      → Signal: ESGScore.post_save fires

5. Layer 7: Group Consolidation
   Signal from ESGScore.post_save (for subsidiary) triggers:
   ① Get parent organization "Acme Group"
   
   ② Recalculate group score:
      - Acme Lagos: 60.1 (updated)
      - Acme Abuja: 55.0
      - Acme Ibadan: 58.0
      - Group average: 57.7 → 58.2
   
   ③ Update parent ESGScore
   
   ④ If parent's parent exists (grandparent), cascade up
      → Signal: ESGScore.post_save fires again (for parent)

6. Layer 8: Report Invalidation
   Signals from Steps 4 & 5 trigger:
   ① Find all reports for org and parents:
      - Org-level reports
      - Parent group reports
      - Grandparent reports (if exists)
   
   ② Mark each report as expired:
      - report.expires_at = now() (immediate expiration)
   
   ③ On next GET /api/v1/reports/{id}/:
      - Detect expired status
      - Regenerate report with fresh data
      - Reset expires_at = now() + 1 hour

Timeline: All steps complete in < 100ms
Result: Single data point update cascades through all 8 layers
```

---

## Key Models & Relationships

### Core Relationships Diagram

```
Organization (Hierarchy Root)
├─ parent ──→ Organization (self-reference)
├─ framework_assignments ──→ OrganizationFramework
│  └─ framework ──→ RegulatoryFramework
│
├─ compliance_gaps ──→ ComplianceGapPriority
│  ├─ framework ──→ RegulatoryFramework
│  └─ requirement ──→ FrameworkRequirement
│
├─ compliance_recommendations ──→ ComplianceRecommendation
│  ├─ framework ──→ RegulatoryFramework
│  └─ requirement ──→ FrameworkRequirement
│
├─ framework_readiness ──→ FrameworkReadiness
│  ├─ framework ──→ RegulatoryFramework
│  └─ reporting_period ──→ ReportingPeriod
│
├─ esg_scores ──→ ESGScore
│  └─ reporting_period ──→ ReportingPeriod
│
├─ activities ──→ Activity
│  └─ activity_type ──→ ActivityType
│
├─ reports ──→ Report
│  ├─ framework ──→ RegulatoryFramework (optional)
│  └─ reporting_period ──→ ReportingPeriod
│
└─ indicator_values ──→ IndicatorValue
   ├─ indicator ──→ Indicator
   └─ reporting_period ──→ ReportingPeriod


RegulatoryFramework
├─ requirements ──→ FrameworkRequirement
├─ framework_indicators ──→ FrameworkIndicator
│  └─ indicator ──→ Indicator
└─ framework_readiness ──→ FrameworkReadiness


Indicator
├─ framework_mappings ──→ FrameworkIndicator
└─ indicator_values ──→ IndicatorValue


ReportingPeriod
├─ esg_scores ──→ ESGScore
├─ framework_readiness ──→ FrameworkReadiness
└─ indicator_values ──→ IndicatorValue
```

---

## API Endpoints by Layer

### Complete API Reference

#### Layer 1: Organization Hierarchy
```
Organization Management
  POST   /api/v1/organizations/                      Create org
  GET    /api/v1/organizations/                      List orgs (paginated)
  GET    /api/v1/organizations/{id}/                 Get org details
  PATCH  /api/v1/organizations/{id}/                 Update org
  DELETE /api/v1/organizations/{id}/                 Delete org
  GET    /api/v1/organizations/{id}/hierarchy/       Get org tree
  GET    /api/v1/organizations/{id}/subsidiaries/    List direct children
  GET    /api/v1/organizations/{id}/ancestors/       Get parent lineage

Reporting Period Management
  POST   /api/v1/reporting-periods/                  Create period
  GET    /api/v1/reporting-periods/?org={id}         List org's periods
  PATCH  /api/v1/reporting-periods/{id}/             Update period
  DELETE /api/v1/reporting-periods/{id}/             Delete period
```

#### Layer 2: Regulatory Frameworks
```
Framework Management
  GET    /api/v1/frameworks/                         List frameworks
  GET    /api/v1/frameworks/{id}/                    Get framework details
  GET    /api/v1/frameworks/{id}/requirements/       Get requirements
  POST   /api/v1/organizations/{id}/frameworks/      Assign to org
  DELETE /api/v1/organizations/{id}/frameworks/{fw}/ Unassign from org

Framework Requirements
  GET    /api/v1/requirements/                       List all
  GET    /api/v1/requirements/{id}/                  Get requirement details
```

#### Layer 3: Indicators & Data Collection
```
Indicator Management
  GET    /api/v1/indicators/                         List indicators
  GET    /api/v1/indicators/{id}/                    Get indicator details
  GET    /api/v1/indicators/?framework={fw_id}       Filter by framework

Indicator Configuration
  POST   /api/v1/organizations/{id}/indicator-config/
           Configure org's indicators
  GET    /api/v1/organizations/{id}/indicator-config/
           Get org's configuration

Data Submission
  POST   /api/v1/indicator-values/                   Submit data point
  GET    /api/v1/indicator-values/?period={period}   Get submitted values
  PATCH  /api/v1/indicator-values/{id}/              Update value
  DELETE /api/v1/indicator-values/{id}/              Delete value
  GET    /api/v1/organizations/{id}/data-status/     Coverage summary
```

#### Layer 4: Activities
```
Activity Type Catalog
  GET    /api/v1/activity-types/                     List templates
  GET    /api/v1/activity-types/{id}/                Get template details

Activity Management
  POST   /api/v1/activities/                         Create activity
  GET    /api/v1/activities/?org={id}                List org's activities
  PATCH  /api/v1/activities/{id}/                    Update activity
  DELETE /api/v1/activities/{id}/                    Delete activity

Activity Submissions
  POST   /api/v1/activity-submissions/               Submit activity data
  GET    /api/v1/activity-submissions/?period={id}   Get submissions
  PATCH  /api/v1/activity-submissions/{id}/          Update submission

Analytics
  GET    /api/v1/organizations/{id}/activity-impact/ Aggregate impact
  GET    /api/v1/activities/{id}/metrics/            Activity metrics
```

#### Layer 5: Compliance & Intelligence
```
Framework Readiness
  GET    /api/v1/organizations/{id}/framework-readiness/
           Coverage overview (all frameworks)
  GET    /api/v1/organizations/{id}/framework-readiness/{fw}/
           Coverage for specific framework
  GET    /api/v1/organizations/{id}/readiness-history/
           Readiness trend over time

Compliance Gaps
  GET    /api/v1/organizations/{id}/compliance-gaps/  Gap list (paginated)
  GET    /api/v1/organizations/{id}/compliance-gaps/{id}/
           Gap details
  GET    /api/v1/organizations/{id}/gap-analysis/    Detailed analysis
  PATCH  /api/v1/compliance-gaps/{id}/               Update gap status

Recommendations
  GET    /api/v1/organizations/{id}/recommendations/
           Recommendation list
  GET    /api/v1/organizations/{id}/recommendations/{id}/
           Recommendation details
  PATCH  /api/v1/recommendations/{id}/               Update status
  POST   /api/v1/recommendations/{id}/accept/        Accept recommendation
  POST   /api/v1/recommendations/{id}/reject/        Reject recommendation
  POST   /api/v1/recommendations/{id}/mark-completed/
           Mark as completed
```

#### Layer 6: ESG Scoring
```
ESG Scores
  GET    /api/v1/organizations/{id}/esg-score/       Latest score
  GET    /api/v1/organizations/{id}/esg-score/history/
           Score history (with dates)
  GET    /api/v1/organizations/{id}/pillar-breakdown/
           E/S/G detail
  GET    /api/v1/organizations/{id}/esg-score/compare/
           vs benchmarks
  GET    /api/v1/organizations/{id}/esg-score/trend/
           Score trend line
```

#### Layer 7: Group Consolidation
```
Group Analytics
  GET    /api/v1/organizations/{id}/group-dashboard/
           Group dashboard
  GET    /api/v1/organizations/{id}/subsidiary-ranking/
           Subsidiary performance ranking
  GET    /api/v1/organizations/{id}/hierarchy-analytics/
           Full hierarchy view with metrics
  GET    /api/v1/organizations/{id}/consolidation-report/
           Detailed consolidation logic
  GET    /api/v1/organizations/{id}/hierarchy-comparison/
           Compare siblings/peers
```

#### Layer 8: Reports & Disclosure
```
Report Management
  GET    /api/v1/reports/                            List reports
  POST   /api/v1/reports/generate/                   Generate new report
  GET    /api/v1/reports/{id}/                       Get report details
  GET    /api/v1/reports/{id}/download/?format=pdf   Download report
                                    ?format=csv
                                    ?format=json
                                    ?format=html
  DELETE /api/v1/reports/{id}/                       Delete report

Quick Report Endpoints
  GET    /api/v1/reports/esg-summary/                Quick ESG summary
  GET    /api/v1/reports/gaps/                       Quick gap report
  GET    /api/v1/reports/group/                      Quick group report
  GET    /api/v1/reports/framework/{fw}/             Framework report

Report Scheduling (Future)
  POST   /api/v1/reports/schedule/                   Schedule recurring
  GET    /api/v1/reports/scheduled/                  List scheduled
```

---

## Authentication & Authorization

### Authentication Flow

```
1. User Registration
   POST /api/v1/accounts/register/
   {
     "email": "user@company.com",
     "password": "secure_password",
     "first_name": "John",
     "last_name": "Doe"
   }
   → User created, verification email sent

2. Email Verification
   GET /api/v1/accounts/verify/{token}/
   → User email confirmed

3. Login
   POST /api/v1/accounts/login/
   {
     "email": "user@company.com",
     "password": "secure_password"
   }
   → Response:
   {
     "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
     "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
   }

4. Use Access Token
   All requests include:
   Authorization: Bearer {access_token}

5. Refresh Token (when access expires)
   POST /api/v1/accounts/refresh/
   {
     "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
   }
   → New access token issued
```

### Authorization

```
Organization-based access control:

For each API request:
  1. Extract organization_id from URL/body
  2. Check user.organizations (M2M relationship)
  3. Verify user is member of org
  4. Check user role (if role-based access exists)
  5. Grant/deny accordingly

Examples:
  ✓ User can access: /api/v1/organizations/org-uuid/ (is member)
  ✗ User cannot access: /api/v1/organizations/other-org/ (not member)
  ✓ User can view: /api/v1/organizations/org-uuid/esg-score/
  ✗ User cannot modify: /api/v1/organizations/org-uuid/ (no admin role)

Roles (Future Enhancement):
  - ADMIN: Full access to organization
  - MANAGER: Can submit data, view reports
  - VIEWER: Read-only access
  - STAKEHOLDER: Limited to specific reports
```

---

## Error Handling Pattern

### RFC7807 Problem Response

All errors follow RFC7807 Problem Response format:

```
Framework:
{
  "type": "https://totalEsg360.io/problems/validation-error",
  "title": "Validation Error",
  "status": 400,
  "detail": "Organization with this name already exists",
  "instance": "/api/v1/organizations/",
  "timestamp": "2026-04-14T10:30:00Z"
}
```

### Common Error Scenarios

```
400 Bad Request
  "invalid_data"
  "missing_field"
  "framework_not_found"
  "organization_not_found"

401 Unauthorized
  "invalid_token"
  "token_expired"
  "authentication_required"

403 Forbidden
  "permission_denied"
  "not_organization_member"

404 Not Found
  "resource_not_found"

409 Conflict
  "duplicate_entry"
  "state_conflict"

500 Internal Server Error
  "calculation_error"
  "database_error"
```

### Error Response Structure

```python
{
  "type": "about:blank",
  "title": "Not Found",
  "status": 404,
  "detail": "Organization with ID '550e8400...' does not exist",
  "instance": "/api/v1/organizations/550e8400.../",
  "timestamp": "2026-04-14T10:30:00Z",
  "errors": [
    {
      "field": "organization_id",
      "message": "Organization not found"
    }
  ]
}
```

---

## Quick Start Examples

### Example 1: Complete Onboarding

```bash
# 1. Register
curl -X POST http://api.totalesg360.io/api/v1/accounts/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@acme.com",
    "password": "SecurePass123!",
    "first_name": "John",
    "last_name": "Adeyemi"
  }'
→ Response: verification email sent

# 2. Verify email (click link in email)
# → User account activated

# 3. Login
curl -X POST http://api.totalesg360.io/api/v1/accounts/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@acme.com",
    "password": "SecurePass123!"
  }'
→ Response: { "access": "...", "refresh": "..." }

# 4. Create Organization
TOKEN="<access_token>"
curl -X POST http://api.totalesg360.io/api/v1/organizations/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Acme Corporation",
    "sector": "manufacturing",
    "country": "NG",
    "primary_reporting_focus": "NIGERIA",
    "organization_type": "group"
  }'
→ Response: { "id": "org-uuid", "name": "Acme Corporation" }

# 5. Assign Framework
ORG_ID="<org-uuid>"
curl -X POST http://api.totalesg360.io/api/v1/organizations/$ORG_ID/frameworks/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "framework_id": "gri-uuid",
    "is_primary": true
  }'
→ Response: Framework assigned

# 6. Configure Indicators
curl -X POST http://api.totalesg360.io/api/v1/organizations/$ORG_ID/indicator-config/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '[
    {"indicator_id": "gri-305-1", "is_required": true},
    {"indicator_id": "gri-305-2", "is_required": true}
  ]'
→ Response: Indicators configured

# 7. Submit Data
curl -X POST http://api.totalesg360.io/api/v1/indicator-values/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "indicator_id": "gri-305-1",
    "organization_id": "'$ORG_ID'",
    "reporting_period_id": "2026-q1",
    "value": 1250.50,
    "unit": "tCO2e"
  }'
→ Response: Data stored
→ Signals: Layer 5, 6, 7, 8 updates triggered automatically

# 8. Get ESG Score
curl -X GET http://api.totalesg360.io/api/v1/organizations/$ORG_ID/esg-score/ \
  -H "Authorization: Bearer $TOKEN"
→ Response: { "environmental": 62.0, "social": ..., "overall": 58.5 }

# 9. Generate Report
curl -X POST http://api.totalesg360.io/api/v1/reports/generate/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "organization_id": "'$ORG_ID'",
    "report_type": "ESG_SUMMARY",
    "file_format": "pdf"
  }'
→ Response: { "id": "report-uuid", "status": "COMPLETED", "file_url": "..." }

# 10. Download Report
curl -X GET http://api.totalesg360.io/api/v1/reports/<report-uuid>/download/?format=pdf \
  -H "Authorization: Bearer $TOKEN" \
  -o acme_esg_report_2026_q1.pdf
```

### Example 2: Multi-Level Group Reporting

```bash
# Setup hierarchy:
# Acme Group (parent)
# ├── Acme Lagos (subsidiary)
# └── Acme Abuja (subsidiary)

# 1. Create Group
GROUP_ID=$(curl -s -X POST http://api.totalesg360.io/api/v1/organizations/ \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"name": "Acme Group", "organization_type": "group", ...}' | jq -r '.id')

# 2. Create subsidiaries
LAGOS_ID=$(curl -s -X POST http://api.totalesg360.io/api/v1/organizations/ \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"parent_id": "'$GROUP_ID'", "name": "Acme Lagos", ...}' | jq -r '.id')

ABUJA_ID=$(curl -s -X POST http://api.totalesg360.io/api/v1/organizations/ \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"parent_id": "'$GROUP_ID'", "name": "Acme Abuja", ...}' | jq -r '.id')

# 3. Submit data for each subsidiary
# Each triggers Layer 6 (ESG score) → Layer 7 (group rollup) → Layer 8 (reports)

# 4. Get Group Dashboard
curl -X GET http://api.totalesg360.io/api/v1/organizations/$GROUP_ID/group-dashboard/ \
  -H "Authorization: Bearer $TOKEN"
→ Response: Group-level aggregation with subsidiary breakdown

# 5. Get Ranking
curl -X GET http://api.totalesg360.io/api/v1/organizations/$GROUP_ID/subsidiary-ranking/ \
  -H "Authorization: Bearer $TOKEN"
→ Response: Lagos (64.0), Abuja (55.0) - ranked

# 6. Generate Group Consolidation Report
curl -X POST http://api.totalesg360.io/api/v1/reports/generate/ \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "organization_id": "'$GROUP_ID'",
    "report_type": "GROUP",
    "file_format": "pdf"
  }'
→ Response: Consolidated report with all subsidiaries
```

---

## Troubleshooting & Common Issues

### Issue: Data not appearing in reports

```
Checklist:
1. Verify indicator has been submitted
   GET /api/v1/indicator-values/?indicator={id}&org={org_id}

2. Check if framework is assigned
   GET /api/v1/organizations/{id}/framework-readiness/

3. Verify reporting period matches
   GET /api/v1/reporting-periods/?org={id}

4. Check readiness calculation
   GET /api/v1/organizations/{id}/framework-readiness/{fw_id}/
   → Should show coverage %, covered_requirements count

5. Verify ESG score was calculated
   GET /api/v1/organizations/{id}/esg-score/
   → Should have environmental, social, governance scores

6. Force report regeneration
   DELETE /api/v1/reports/{id}/  (if cached)
   POST /api/v1/reports/generate/  (create new)
```

### Issue: Group scores not cascading

```
Checklist:
1. Verify parent_id is set on subsidiary
   GET /api/v1/organizations/{subsidiary_id}/
   → Check parent field

2. Submit data to subsidiary first
   POST /api/v1/indicator-values/ (subsidiary_id)
   → Triggers: Layer 5 → Layer 6 (ESG calc for subsidiary)

3. Check if parent ESG score updated
   GET /api/v1/organizations/{parent_id}/esg-score/
   → Should be more recent than subsidiary data

4. Verify chain:
   Subsidiary IndicatorValue (2026-04-14 10:00)
     ↓ 5ms
   Subsidiary ESGScore (2026-04-14 10:00:05)
     ↓ 5ms
   Parent ESGScore (2026-04-14 10:00:10)
```

### Issue: Reports expiring too quickly

```
Current behavior:
  - Report generated with expires_at = now() + 1 hour
  - If data changes, report marked expired immediately
  - On next access, regenerated

To force regeneration:
  DELETE /api/v1/reports/{id}/
  POST /api/v1/reports/generate/ (with same parameters)

Note: 1-hour TTL can be configured in settings.
```

---

## Next Steps & Future Enhancements

1. **Role-Based Access Control (RBAC)**
   - Implement granular permissions
   - Support multi-role users

2. **Reporting Automation**
   - Scheduled report generation
   - Email delivery of reports
   - Batch reporting

3. **Advanced Analytics**
   - Trend analysis
   - Peer benchmarking
   - Predictive scoring

4. **Integration APIs**
   - Webhook support for external updates
   - Third-party data connector framework
   - Real-time data streaming

5. **Enhanced Visualizations**
   - Interactive dashboards
   - Custom charting
   - Data exploration tools

---

## Support & Documentation

- **API Documentation**: /docs/ (Swagger/OpenAPI)
- **Developer Guide**: See individual layer docs
- **Postman Collection**: `/postman/collections/`
- **Support Email**: support@totalEsg360.io

---

**Document Version**: 1.0  
**Last Updated**: April 14, 2026  
**Status**: Complete & Production Ready ✅
