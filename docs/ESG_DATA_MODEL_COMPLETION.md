# ESG Data Model Completion

## Scope
Implemented missing computation and structure layers requested for the ESG data model:
- Indicator dependency graph
- Indicator-based emission factor structure
- Calculation engine service
- Organization activation sync reinforcement
- Activity -> Indicator linkage alignment in tests

## 1. Indicator Dependency System
Added `IndicatorDependency` model to define computational lineage:
- `parent_indicator`
- `child_indicator`
- `relationship_type` (`aggregation`, `conversion`)
- `weight` (optional)
- `is_active`

Files:
- `src/indicators/models/indicator_dependency.py`
- `src/indicators/models/__init__.py`
- `src/indicators/migrations/0008_indicatordependency.py`

## 2. Emission Factor System (Indicator-Aware)
Extended existing `EmissionFactor` model in a backward-compatible way:
- Added `indicator` (optional FK)
- Added `factor_value`
- Added `unit_input`
- Added `unit_output`
- Made `activity_type` optional to support indicator-level factors directly
- Added `effective_factor_value` property

Files:
- `src/emissions/models/emission_factor.py`
- `src/emissions/migrations/0003_emissionfactor_indicator_fields.py`

## 3. Calculation Engine
Implemented `calculate_indicator_value(indicator, period, org)` in service layer.

Behavior:
- **PRIMARY indicators**: computes from dependencies using conversion factors where required
- **DERIVED indicators**: aggregates child indicators via dependencies
- **INPUT indicators**: aggregates existing `IndicatorValue`
- Persists computed value to `IndicatorValue` (facility=None) by default

Files:
- `src/indicators/services/calculation_engine.py`
- `src/indicators/services/__init__.py`

## 4. Activity Structure Alignment
Current structure already supports:
- Generic indicators (`Indicator`)
- Specific activities (`ActivityType`) linked via `ActivityType -> Indicator`

Updated emissions integration tests to align with required indicator linkage.

Files:
- `src/emissions/tests/test_integration.py`
- `src/emissions/tests/test_tasks_and_api.py`

## 5. Organization Activation Layer
Reinforced activation flow so framework selection updates trigger indicator sync explicitly.

Flow:
- Framework assignments updated
- Primary framework normalized
- `schedule_sync_for_org(organization)` called
- `OrganizationIndicator` entries synced from active mappings

File:
- `src/organizations/services/framework_selection.py`

## 6. Data Flow Outcome
Implemented flow supports:
- `ActivitySubmission` -> `IndicatorValue` (input indicators)
- Dependencies + factors -> computed primary indicators
- Dependencies -> derived totals
- Framework mappings -> compliance-ready indicator activation and reporting

## Validation
Executed targeted tests:
- `src.indicators.tests.test_calculation_engine`
- `src.emissions.tests.test_integration`
- `src.emissions.tests.test_tasks_and_api`
- `src.organizations.tests.test_framework_selection_api`

Result: tests passed in targeted run.

Note: Existing unrelated log noise remains from ESG consolidation task kwargs mismatch in `esg_scoring.signals`, but did not fail these tests.
