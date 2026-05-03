# ESG Pipeline Performance Optimizations

Date: 2026-05-03

## Scope

This change set optimized two performance hotspots in the ESG indicator pipeline without changing business logic, signal ordering, recalculation behavior, or ESG scoring behavior.

## What Changed

### 1. Optimized `get_affected_indicators`

File: `src/indicators/services/calculation_engine.py`

Before:
- The DFS walked upward through `IndicatorDependency`
- Each DFS step queried dependencies for the current node
- Each parent indicator was fetched individually with `Indicator.objects.get(...)`
- This created an N+1 query pattern as the dependency graph grew

After:
- All active dependencies are loaded once with a single query:
  - `IndicatorDependency.objects.filter(is_active=True).values_list("child_indicator_id", "parent_indicator_id")`
- An in-memory parent adjacency map is built
- DFS runs entirely in memory using indicator IDs
- All affected indicators are bulk-fetched at the end with one query:
  - `Indicator.objects.filter(id__in=result_ids)`

Result:
- No per-node database lookups during DFS
- Dependency resolution now uses one dependency query plus one indicator query

### 2. Skipped target evaluation for indicators without active targets

File: `src/indicators/signals.py`

Before:
- The signal evaluated targets for every indicator returned by `get_affected_indicators(...)`
- Indicators with no matching targets still went through `evaluate_targets_for_indicator(...)`

After:
- The signal first collects affected indicator IDs
- It then bulk-loads only the indicator IDs that actually have active targets for the current organization
- Target evaluation is only executed for indicators in that filtered set

Result:
- No wasted target evaluation calls for irrelevant indicators
- Behavior remains unchanged for indicators that do have targets

## What Was Not Changed

The following were intentionally left unchanged:

- `recalculate_dependent_indicators`
- The thread-local signal guard logic
- ESG scoring trigger order and Celery chain
- Business rules around indicator recalculation, target evaluation, or compliance

## Signal Flow After Optimization

The runtime flow remains:

1. `IndicatorValue` is saved
2. Dependent indicators are recalculated
3. Targets are evaluated for affected indicators that actually have active targets
4. ESG scoring tasks are queued

## Validation Performed

The following checks were run successfully:

- `python manage.py check`
- `python manage.py shell -c "import indicators.signals; import indicators.services.calculation_engine; print('OK')"`

## Files Changed

- `src/indicators/services/calculation_engine.py`
- `src/indicators/signals.py`
- `docs/ESG_PIPELINE_PERFORMANCE_OPTIMIZATIONS.md`
