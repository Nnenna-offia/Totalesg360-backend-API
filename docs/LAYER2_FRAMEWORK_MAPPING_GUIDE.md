# Layer 2 — Indicator Framework Mapping Engine

**Comprehensive guide for mapping ESG indicators to compliance frameworks and requirements.**

---

## Overview

The **Indicator Framework Mapping Engine** connects ESG indicators to regulatory framework requirements, enabling:

- **Multi-framework reporting** (GRI, IFRS, SASB, TCFD, NGX, NESREA, etc.)
- **Compliance gap analysis** (which requirements are uncovered)
- **Framework matrix** (map indicators to multiple requirements)
- **Coverage tracking** (real-time compliance metrics)
- **Enterprise ESG mapping** (organization-level compliance status)

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│         RegulatoryFramework (GRI, IFRS, SASB, etc.)     │
└────────────────────┬────────────────────────────────────┘
                     │
                     ├─ FrameworkRequirement (GRI 305-1, IFRS S2-1, etc.)
                     │  ├─ Code: GRI 305-1
                     │  ├─ Title: Direct GHG Emissions Disclosure
                     │  ├─ Pillar: Environmental / Social / Governance
                     │  ├─ Is Mandatory: true
                     │  └─ Status: active/deprecated/archived
                     │
                     └─ IndicatorFrameworkMapping
                        ├─ Indicator: Scope 1 Emissions
                        ├─ Requirement: GRI 305-1
                        ├─ Mapping Type: primary/supporting/reference
                        ├─ Is Primary: true
                        ├─ Coverage: 100%
                        └─ Rationale: "..."

┌─────────────────────────────────────────────────────────┐
│              Organization Framework Status               │
├─────────────────────────────────────────────────────────┤
│ GRI (Active)                                             │
│ ├─ Total Requirements: 45                               │
│ ├─ Covered: 38 (84%)                                    │
│ ├─ Gaps: 7 uncovered requirements                       │
│ └─ Status: Substantial coverage                         │
│                                                         │
│ IFRS (Active)                                            │
│ ├─ Total Requirements: 28                               │
│ ├─ Covered: 24 (85%)                                    │
│ ├─ Gaps: 4 uncovered requirements                       │
│ └─ Status: Substantial coverage                         │
└─────────────────────────────────────────────────────────┘
```

---

## Data Models

### 1. FrameworkRequirement

**Purpose:** Defines specific requirements/disclosures within a regulatory framework.

**Fields:**

```python
framework              # ForeignKey(RegulatoryFramework)
code                   # CharField - Unique within framework (e.g., "GRI 305-1")
title                  # CharField - Short title
description            # TextField - Detailed description
pillar                 # CharField - environmental/social/governance
is_mandatory           # BooleanField - Required vs optional
status                 # CharField - active/deprecated/archived
priority               # IntegerField - Display/sorting priority
guidance_url           # URLField - Link to framework documentation
version                # CharField - Requirement version
created_at / updated_at # Timestamps
```

**Unique Constraint:** `(framework, code)`

**Example:**

| Framework | Code      | Title                        | Pillar        | Mandatory |
|-----------|-----------|------------------------------|---------------|-----------|
| GRI       | GRI 305-1 | Direct GHG Emissions         | Environmental | ✓         |
| IFRS      | IFRS S2-1 | Physical Climate Risks       | Environmental | ✓         |
| SASB      | EM-EP-110a| Air Emissions Intensity      | Environmental | ✓         |
| TCFD      | E-1       | Governance Structure         | Governance    | ✓         |
| NGX       | E-1       | Environmental & Social Report| Environmental | ✓         |

---

### 2. IndicatorFrameworkMapping

**Purpose:** Maps indicators to framework requirements, documenting how each indicator satisfies requirements.

**Fields:**

```python
indicator              # ForeignKey(Indicator)
framework              # ForeignKey(RegulatoryFramework)
requirement            # ForeignKey(FrameworkRequirement)
mapping_type           # CharField - primary/supporting/reference
is_primary             # BooleanField - Primary indicator for requirement
rationale              # TextField - How indicator satisfies requirement
coverage_percent       # IntegerField - 0-100% (how much requirement covered)
is_active              # BooleanField - Active/inactive mapping
notes                  # TextField - Additional notes
created_at / updated_at# Timestamps
```

**Unique Constraint:** `(indicator, framework, requirement)`

**Mapping Types:**

- **PRIMARY**: Core requirement satisfaction (typically 100% coverage)
- **SUPPORTING**: Partial/contributing satisfaction (50-99% coverage)
- **REFERENCE**: Informational/contextual (0-49% coverage)

**Example:**

| Indicator           | Framework | Requirement | Type    | Coverage | Primary |
|---------------------|-----------|-------------|---------|----------|---------|
| Scope 1 Emissions   | GRI       | GRI 305-1   | PRIMARY | 100%     | ✓       |
| Scope 1 Emissions   | IFRS      | IFRS S2-1   | PRIMARY | 100%     | ✓       |
| Scope 1 Emissions   | SASB      | EM-EP-110a  | PRIMARY | 100%     | ✓       |
| Total GHG Emissions | GRI       | GRI 305-4   | SUPPORT | 80%      | ✗       |

---

## API Endpoints

### Framework Requirements

**List requirements for a framework:**

```
GET /api/v1/compliance/framework-requirements/by_framework/?framework_id=<uuid>

Response:
{
  "count": 45,
  "results": [
    {
      "id": "uuid",
      "code": "GRI 305-1",
      "title": "Direct GHG Emissions Disclosure",
      "description": "...",
      "pillar": "environmental",
      "is_mandatory": true,
      "status": "active",
      "priority": 1,
      "indicators_mapped": [...],
      "covered_by_count": 3
    }
  ]
}
```

**Get framework coverage statistics:**

```
GET /api/v1/compliance/framework-requirements/coverage/?framework_id=<uuid>

Response:
{
  "framework": {...},
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
    "social": {...},
    "governance": {...}
  }
}
```

---

### Indicator Mappings

**Get all frameworks for an indicator:**

```
GET /api/v1/compliance/indicator-mappings/for_indicator/?indicator_id=<uuid>

Response:
{
  "indicator": {
    "id": "uuid",
    "code": "Scope 1 Emissions",
    "name": "Scope 1 Emissions"
  },
  "frameworks": [
    {
      "framework": {
        "id": "uuid",
        "code": "GRI",
        "name": "Global Reporting Initiative"
      },
      "requirements": [
        {
          "code": "GRI 305-1",
          "title": "Direct GHG Emissions",
          "mapping_type": "primary",
          "coverage_status": "full",
          "is_primary": true,
          "coverage_percent": 100
        }
      ]
    }
  ],
  "total_frameworks": 4
}
```

**Get all indicators for a framework:**

```
GET /api/v1/compliance/indicator-mappings/for_framework/?framework_id=<uuid>

Response:
{
  "framework": {...},
  "indicators": [
    {
      "indicator": {
        "id": "uuid",
        "code": "Scope 1 Emissions",
        "name": "Scope 1 GHG Emissions",
        "pillar": "environmental"
      },
      "mappings": [
        {
          "id": "uuid",
          "requirement": "GRI 305-1",
          "mapping_type": "primary",
          "coverage_percent": 100
        }
      ]
    }
  ],
  "total_indicators": 28
}
```

**Find compliance gaps:**

```
GET /api/v1/compliance/indicator-mappings/gaps/?organization_id=<uuid>&framework_id=<uuid>

Response:
{
  "organization": {
    "id": "uuid",
    "name": "Total ESG Company"
  },
  "framework": {...},
  "gaps": {
    "environmental": [
      {
        "code": "GRI 305-5",
        "title": "Energy Reduction Initiatives",
        "description": "...",
        "is_mandatory": true
      }
    ],
    "social": [],
    "governance": [...]
  },
  "total_gaps": 7
}
```

---

### Organization Frameworks

**Get organization's compliance status:**

```
GET /api/v1/compliance/organization-frameworks/status/

Response:
[
  {
    "organization_framework": {
      "id": "uuid",
      "is_primary": true,
      "is_enabled": true,
      "assigned_at": "2025-04-12T..."
    },
    "framework": {
      "id": "uuid",
      "code": "GRI",
      "name": "Global Reporting Initiative"
    },
    "total_requirements": 45,
    "covered_requirements": 38,
    "uncovered_requirements": 7,
    "coverage_percent": 84.4,
    "is_primary": true
  },
  {
    "framework": {...},
    "total_requirements": 28,
    "covered_requirements": 24,
    "uncovered_requirements": 4,
    "coverage_percent": 85.7,
    "is_primary": false
  }
]
```

**Get all assigned frameworks:**

```
GET /api/v1/compliance/organization-frameworks/all/

Response:
[
  {
    "organization_framework": {...},
    "framework": {...},
    "coverage": {
      "total_requirements": 45,
      "covered_requirements": 38,
      "coverage_percent": 84.4,
      "by_pillar": {...}
    }
  }
]
```

---

## Selectors (Query Functions)

### get_organization_frameworks(organization)

Get all active frameworks assigned to an organization.

```python
from compliance.selectors import get_organization_frameworks

frameworks = get_organization_frameworks(org)
for org_fw in frameworks:
    print(f"{org_fw.framework.name} - Primary: {org_fw.is_primary}")
```

---

### get_framework_indicators(framework)

Get all indicators mapped to a framework with their coverage details.

```python
from compliance.selectors import get_framework_indicators

indicators = get_framework_indicators(gri_framework)
for indicator in indicators:
    mappings = indicator.regulatory_requirement_mappings.all()
    print(f"{indicator.name}: {len(mappings)} requirements")
```

---

### get_indicator_frameworks(indicator)

Get all frameworks an indicator is mapped to.

```python
from compliance.selectors import get_indicator_frameworks

frameworks = get_indicator_frameworks(scope1_emissions_indicator)
for item in frameworks:
    print(f"{item['framework'].code}: {item['requirement'].code}")
```

---

### get_framework_requirements(framework)

Get all active requirements for a framework with coverage stats.

```python
from compliance.selectors import get_framework_requirements

requirements = get_framework_requirements(gri_framework)
for req in requirements:
    print(f"{req.code}: covered by {req.covered_by_count} indicators")
```

---

### get_framework_coverage(framework)

Get overall coverage statistics for a framework.

```python
from compliance.selectors import get_framework_coverage

coverage = get_framework_coverage(gri_framework)
print(f"Coverage: {coverage['coverage_percent']}%")
print(f"Covered: {coverage['covered_requirements']}/{coverage['total_requirements']}")
print(f"By pillar: {coverage['by_pillar']}")
```

---

### get_uncovered_requirements(organization, framework)

Find requirements not covered by organization's indicators (gap analysis).

```python
from compliance.selectors import get_uncovered_requirements

gaps = get_uncovered_requirements(org, gri_framework)
for gap in gaps:
    print(f"Missing: {gap.code} - {gap.title}")
```

---

### get_organization_framework_status(organization)

Get compliance status across all organization's frameworks.

```python
from compliance.selectors import get_organization_framework_status

status = get_organization_framework_status(org)
for fw_status in status:
    print(f"{fw_status['framework'].name}: {fw_status['coverage_percent']}% covered")
```

---

### get_indicator_requirement_gaps(indicator, framework)

Find requirements related to indicator's pillar that aren't covered.

```python
from compliance.selectors import get_indicator_requirement_gaps

gaps = get_indicator_requirement_gaps(scope1_emissions, gri_framework)
for gap in gaps:
    print(f"Related uncovered: {gap.code}")
```

---

## Admin Interface

### Framework Requirements Admin

Navigate to: **Django Admin > Compliance > Framework Requirements**

**Features:**

- List by framework, pillar, status
- Search by code, title, description
- Color-coded mandatory/optional status
- Guidance URL links
- Bulk actions for status changes

**Customizations:**

- Filter by pillar (E/S/G)
- Filter by status (active/deprecated/archived)
- Search requirements by code or title
- Sort by priority, pillar, code

---

### Indicator-Framework Mappings Admin

Navigate to: **Django Admin > Compliance > Indicator-Framework Mappings**

**Features:**

- List with coverage status indicators
- Color-coded coverage status (full/substantial/partial/minimal)
- Primary/supporting/reference mapping types
- Filter by framework, pillar, mapping type
- Search by indicator, requirement, framework codes

**Customizations:**

- Toggle mapping type (PRIMARY/SUPPORTING/REFERENCE)
- Edit coverage percentage
- Add mapping rationale
- Mark as primary/supporting
- Status for active/inactive mappings

---

## Use Cases

### Use Case 1: Gap Analysis

**Identify compliance gaps for organization and framework:**

```python
from compliance.selectors import get_uncovered_requirements

org = Organization.objects.get(code="TGI")
gri = RegulatoryFramework.objects.get(code="GRI")

gaps = get_uncovered_requirements(org, gri)
print(f"Total gaps: {gaps.count()}")

for gap in gaps:
    print(f"  - {gap.code}: {gap.title}")
```

---

### Use Case 2: Framework Alignment Report

**Generate compliance report for specific framework:**

```python
from compliance.selectors import get_framework_coverage, get_framework_indicators

framework = RegulatoryFramework.objects.get(code="IFRS")
coverage = get_framework_coverage(framework)
indicators = get_framework_indicators(framework)

print(f"Framework: {framework.name}")
print(f"Coverage: {coverage['coverage_percent']}%")
print(f"Indicators: {len(indicators)}")
print(f"By Pillar:")
for pillar, stats in coverage['by_pillar'].items():
    print(f"  {pillar}: {stats['coverage_percent']}%")
```

---

### Use Case 3: Indicator-to-Requirement Mapping

**Find all requirements satisfied by a single indicator:**

```python
from compliance.selectors import get_indicator_frameworks

indicator = Indicator.objects.get(code="Scope1Emissions")
frameworks = get_indicator_frameworks(indicator)

for item in frameworks:
    print(f"{item['framework'].name}:")
    print(f"  Requirement: {item['requirement'].code}")
    print(f"  Type: {item['mapping_type']}")
    print(f"  Coverage: {item['coverage_status']}")
```

---

### Use Case 4: Organization Multi-Framework Status

**Track organization's compliance across multiple frameworks:**

```python
from compliance.selectors import get_organization_framework_status

org = Organization.objects.get(code="TGI")
status = get_organization_framework_status(org)

for fw_status in status:
    print(f"{fw_status['framework'].name}:")
    print(f"  Coverage: {fw_status['coverage_percent']}%")
    print(f"  Covered: {fw_status['covered_requirements']}/{fw_status['total_requirements']}")
    print(f"  Primary: {'Yes' if fw_status['is_primary'] else 'No'}")
```

---

## Data Examples

### Sample Framework Requirements

| Framework | Code      | Title                          | Pillar        | Mandatory |
|-----------|-----------|--------------------------------|---------------|-----------|
| GRI       | 305-1     | Direct (Scope 1) GHG Emissions | Environmental | Yes       |
| GRI       | 305-2     | Energy Indirect Emissions      | Environmental | Yes       |
| GRI       | 305-5     | Reduction of GHG Emissions     | Environmental | Yes       |
| IFRS      | S2-1      | Transition Plan Details        | Environmental | Yes       |
| IFRS      | S1-5      | Board Gender Diversity         | Social        | Yes       |
| SASB      | EM-EP-110a| Air Emissions Intensity        | Environmental | Yes       |
| TCFD      | Governance| Governance Structure           | Governance    | Yes       |
| NGX       | ESG-001   | Board Composition              | Governance    | Yes       |

### Sample Indicator Mappings

| Indicator Code    | Framework | Requirement | Type    | Coverage |
|-------------------|-----------|-------------|---------|----------|
| SCOPE1_GHG        | GRI       | 305-1       | PRIMARY | 100%     |
| SCOPE1_GHG        | IFRS      | S2-1        | PRIMARY | 100%     |
| SCOPE1_GHG        | SASB      | EM-EP-110a  | PRIMARY | 100%     |
| ENERGY_REDUCTION  | GRI       | 305-5       | PRIMARY | 100%     |
| ENERGY_REDUCTION  | IFRS      | S2-2        | SUPPORT | 80%      |
| BOARD_DIVERSITY   | NGX       | ESG-001     | PRIMARY | 100%     |
| BOARD_DIVERSITY   | TCFD      | Governance  | SUPPORT | 60%      |

---

## Integration with ESG Scoring

The Framework Mapping Engine integrates with Layer 2 ESG Scoring:

1. **Compliance-driven scoring** - Weight indicators by framework requirements
2. **Gap-driven prioritization** - Focus on uncovered requirements
3. **Framework-specific reports** - Generate reports by framework
4. **Compliance dashboard** - Show framework coverage metrics

---

## Summary

| Component | Count | Purpose |
|-----------|-------|---------|
| Models | 2 | Framework requirements & indicator mappings |
| Selectors | 8 | Query functions for framework relationships |
| ViewSets | 4 | REST API endpoints |
| Serializers | 10 | Data serialization/validation |
| Admin Panels | 2 | Django admin interfaces |
| API Endpoints | 15+ | Complete CRUD & analysis operations |

**Status:** ✅ Production-Ready

