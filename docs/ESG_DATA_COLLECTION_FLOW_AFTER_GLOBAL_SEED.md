# ESG Data Collection Flow After Global Seed

## Purpose
This document describes the current end-to-end ESG data collection flow after global ESG master data has been seeded with:

- frameworks
- framework requirements
- indicators
- indicator-framework mappings
- activity types
- traceability relationships
- emission factor support

Primary seed command:

```bash
python manage.py seed_esg_master_data
```

Related schema/setup now present in the system:

- `IndicatorFrameworkMapping`
- `IndicatorDependency`
- `EmissionFactor`
- `OrganizationIndicator`
- `IndicatorValue`
- `ActivityType -> Indicator`

---

## 1. Global Seed Outcome

After global seeding, the platform has a global ESG catalog with the following layers.

### 1.1 Framework Layer
Global frameworks exist, for example:

- GRI
- ISSB / IFRS S2
- TCFD
- SASB
- CDP
- NESREA
- CBN ESG
- NSE ESG
- FMENV

Each framework has seeded `FrameworkRequirement` rows.

### 1.2 Indicator Layer
Indicators are globally available in three logical roles.

#### Input Indicators
Examples:

- `S1-DIESEL-L`
- `S1-LPG-KG`
- `S1-NATGAS-M3`
- `S1-REFRIG-KG`
- `S2-ELEC-KWH`
- `S3-FERT-KG`
- `S3-TRANSPORT-KM`
- `S3-WASTE-M3`
- `S3-FEED-KG`

These represent raw operational measurements.

#### Primary Indicators
Examples:

- `ENV-S1-EMISSIONS-TCO2E`
- `ENV-S2-EMISSIONS-TCO2E`
- `ENV-S3-EMISSIONS-TCO2E`

These are the main compliance-facing emissions indicators.

#### Derived Indicators
Example:

- `ENV-TOTAL-EMISSIONS-TCO2E`

This is used for analytics and rollups rather than as the main compliance anchor.

### 1.3 Mapping Layer
`IndicatorFrameworkMapping` links indicators to framework requirements.

Current meaning:

- `PRIMARY`: requirement-satisfying derived indicator
- `SECONDARY`: supporting input indicator
- `DERIVED`: optional analytic/rollup mapping

### 1.4 Activity Layer
`ActivityType` is already linked to a global indicator.

Examples:

- Diesel Generator Usage -> `S1-DIESEL-L`
- LPG Usage -> `S1-LPG-KG`
- Grid Electricity Consumption -> `S2-ELEC-KWH`
- Transport Logistics -> `S3-TRANSPORT-KM`

This means activities are specific collection inputs, while indicators remain the generic KPI layer.

### 1.5 Dependency Layer
`IndicatorDependency` defines how indicators depend on each other.

Examples:

- Scope 1 emissions <- Diesel consumption
- Scope 1 emissions <- LPG consumption
- Scope 2 emissions <- Electricity consumption
- Total emissions <- Scope 1 emissions
- Total emissions <- Scope 2 emissions
- Total emissions <- Scope 3 emissions

### 1.6 Factor Layer
`EmissionFactor` supports emission conversion.

It now supports both:

- activity-based factor lookup
- indicator-based factor lookup

This allows raw input indicators to be converted into emissions values.

---

## 2. Activation Flow Per Organization

Global seed does not automatically enable everything for every organization.

An organization activates the seeded catalog through framework selection.

### 2.1 Organization Selects Frameworks
The organization updates `OrganizationFramework` assignments.

Flow:

```text
Organization selects frameworks
    -> OrganizationFramework updated
    -> primary framework normalized
    -> org indicator sync scheduled
```

### 2.2 Organization Indicators Are Derived
When framework assignments are enabled, `OrganizationIndicator` rows are synced from active mappings.

This gives the organization only the indicators relevant to its enabled frameworks.

Result:

- only selected-framework indicators become active at org level
- compliance-facing indicators are available for the org
- supporting input indicators are also available where mapped

---

## 3. Reporting Period Source Of Truth

Reporting periods are controlled only by organization ESG settings.

```text
Organization ESG settings
    -> reporting_frequency
    -> active reporting period
    -> activity and indicator submissions attach to that period
```

Important:

- `ActivityType.collection_frequency` is planning/UI only
- it does not control reporting periods
- submissions use organization reporting period resolution

---

## 4. Data Collection Flow

## Step 1: User Collects Operational Data
A user collects a real-world operational input.

Examples:

- litres of diesel used
- kg of LPG consumed
- kWh of electricity purchased
- km of transport traveled
- kg of fertilizer applied
- m3 of waste disposed

## Step 2: User Submits an Activity
User submits through the activity submission flow.

```text
POST activity submission
    -> validate org membership
    -> resolve reporting period from organization settings
    -> validate ActivityType
    -> create ActivitySubmission
```

Stored model:

- `ActivitySubmission`

Key relation:

- `ActivitySubmission.activity_type`
- `ActivityType.indicator`

So each submitted activity is already tied to a generic input indicator.

## Step 3: Input Indicator Value Is Aggregated
After activity submission, activity aggregation updates `IndicatorValue` for the linked input indicator.

```text
ActivitySubmission
    -> ActivityType.indicator
    -> aggregate total for org + period (+ facility when applicable)
    -> upsert IndicatorValue
```

Stored model:

- `IndicatorValue`

At this point the system has normalized operational data into the indicator layer.

---

## 5. Emissions Calculation Flow

## Step 4: Emission Calculation Uses Traceability + Factors
Emission calculation now has explicit traceability support.

Current linkage in service layer:

- Diesel -> Scope 1
- LPG -> Scope 1
- Natural gas -> Scope 1
- Refrigerant leakage -> Scope 1
- Electricity -> Scope 2
- Fertilizer -> Scope 3
- Transport -> Scope 3
- Waste -> Scope 3
- Feed -> Scope 3

The calculation service resolves:

1. input indicator
2. expected derived scope
3. matching emission factor
4. resulting `CalculatedEmission`

Stored model:

- `CalculatedEmission`

This is the raw emissions-computation layer tied to submitted activities.

---

## 6. Indicator Calculation Engine

The indicator calculation engine is now available for dependency-based indicator computation.

Service:

- `calculate_indicator_value(indicator, period, org)`

### 6.1 For Input Indicators
The engine reads existing aggregated `IndicatorValue` rows.

```text
Input indicator
    -> aggregate IndicatorValue rows
    -> return current value
```

### 6.2 For Primary Indicators
The engine follows `IndicatorDependency` rows and applies conversion logic.

```text
Primary indicator
    -> find child input indicators
    -> fetch child values
    -> apply emission factor
    -> sum result
    -> write IndicatorValue for primary indicator
```

Example:

```text
Scope 1 emissions
    = Diesel * factor
    + LPG * factor
    + Natural gas * factor
    + Refrigerant leakage * factor
```

### 6.3 For Derived Indicators
The engine aggregates parent-level indicators.

```text
Total emissions
    = Scope 1 emissions
    + Scope 2 emissions
    + Scope 3 emissions
```

---

## 7. Compliance Flow

Once indicators exist for an organization and a reporting period, compliance can be evaluated.

### 7.1 Primary Mappings Drive Requirement Coverage
Each framework requirement must have at least one primary mapped indicator.

This means compliance reporting is anchored on the primary emissions indicators, not on raw inputs.

### 7.2 Secondary Mappings Provide Traceability
Secondary input mappings do not replace primary coverage.

They exist to provide:

- audit traceability
- evidence lineage
- operational explanation of how the primary value was produced

### 7.3 Dynamic Coverage
Mapping coverage is not seeded as complete.

Coverage is computed dynamically from indicator values/data presence.

So compliance becomes:

```text
Framework requirement
    <- PRIMARY indicator exists
    <- org indicator is active
    <- indicator value exists in reporting period
    -> requirement considered covered in runtime evaluation
```

---

## 8. End-to-End Flow Summary

```text
seed_esg_master_data
    -> global frameworks
    -> global requirements
    -> global indicators
    -> global mappings
    -> global activity types

Organization selects frameworks
    -> OrganizationFramework updated
    -> OrganizationIndicator sync

User submits activity data
    -> ActivitySubmission created
    -> input IndicatorValue aggregated
    -> CalculatedEmission computed

Calculation engine runs
    -> PRIMARY indicators computed from inputs + emission factors
    -> DERIVED indicators computed from primary indicators

Compliance layer reads mapped indicators
    -> framework coverage
    -> requirement satisfaction
    -> reporting readiness
```

---

## 9. Actual Data Flow Graph

```text
Activity
    -> ActivitySubmission
    -> Input IndicatorValue
    -> CalculatedEmission
    -> Primary IndicatorValue
    -> Derived IndicatorValue
    -> Framework compliance / reporting / scoring
```

Expanded:

```text
ActivityType
    -> linked Input Indicator
    -> submitted by user
    -> aggregated into IndicatorValue
    -> converted with EmissionFactor
    -> rolled into PRIMARY emissions indicator
    -> rolled into DERIVED total emissions indicator
    -> evaluated through IndicatorFrameworkMapping
    -> used for compliance and ESG analytics
```

---

## 10. What Is Automatic vs Manual

### Automatic

- global data seeding
- framework-to-org indicator activation sync
- activity-to-input-indicator aggregation
- activity-level emission calculation
- reporting period resolution from org settings

### Available But Needs Invocation In Workflow

- dependency-based `calculate_indicator_value(...)` for primary and derived indicator recomputation

This service is implemented and ready, but the exact orchestration point can still be expanded depending on whether computation should run:

- on every activity submission
- on period lock
- on demand
- in background tasks

---

## 11. Operational Meaning After Seed

After global seeding, the system is no longer a flat catalog.

It becomes a structured ESG pipeline:

- frameworks define what matters
- mappings define what satisfies it
- activities collect raw evidence
- indicators normalize measurements
- factors convert measurements to emissions
- dependencies compute primary and derived ESG values
- organization activation limits scope to selected frameworks
- reporting periods keep all data aligned in time

---

## 12. Current Final State

With the current implementation, the seeded system supports:

- global ESG master data
- multi-framework compliance mapping
- organization-specific activation
- activity-based collection
- input indicator normalization
- emissions conversion support
- indicator dependency graph
- primary and derived indicator computation
- compliance-ready reporting structure

This is the current post-seed data collection architecture in the codebase.
