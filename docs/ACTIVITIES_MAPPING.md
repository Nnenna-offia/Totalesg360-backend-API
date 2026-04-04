# Activities Mapping: models, fields, and data flow

**Purpose:** Describe how `ActivityType`, `Scope`, `Indicator`, and activity submissions relate and how data flows between them.

**Key Entities**
- **`ActivityType`**: Canonical activity definition. Core fields:
  - **`name`**: Human label.
  - **`unit`**: Measurement unit (auto-synced from linked `Indicator`).
  - **`scope`**: FK to `Scope` that groups related activities.
  - **`indicator`**: FK to `indicators.Indicator` (required).
  - **`is_active`**: Metadata.

- **`Scope`**: Lightweight grouping (e.g., emissions, waste). Fields: `code`, `name`, `description`.

- **`Indicator`**: Canonical metric definition. Fields: `code`, `name`, `unit`, `collection_method`, `data_type`, etc. If `collection_method` is `activity`, the indicator is intended to be driven by activity submissions.

- **Activity Submission** (domain-level concept implemented in `submissions` app): Links an `ActivityType` to a `ReportingPeriod`, `Facility`, and `Organization` and records a `value` (and `unit`).

**Database tables**
- `activities_activitytype` → `ActivityType` table.
- `activities_scope` → `Scope` table.
- `indicators_indicator` → `Indicator` table.
- Submissions live in `submissions_*` tables (see `src/submissions`).

**Mapping & Rules**
- `ActivityType.indicator` is required: every activity type maps to one indicator. This enforces a 1→1 canonical mapping used for reporting and analytics.

-- `ActivityType.unit` is denormalized but authoritative: on save, `ActivityType.unit` is automatically set from `Indicator.unit` to keep the canonical unit available directly on the activity for fast access.

**APIs & UI mapping**
- The Activities API surface is documented in [docs/ACTIVITIES_ENDPOINTS.md](docs/ACTIVITIES_ENDPOINTS.md) — endpoints for managing activity types, scopes, and submissions reflect the model relationships above.
- When creating an `ActivityType` via the API, supply `indicator` (indicator id) and `scope` (scope id). The response will include the `unit` (synced from the indicator).

**Behavioral examples**
- Create flow: Admin creates `Indicator` → create `ActivityType` referencing that `Indicator` and a `Scope` → `ActivityType.unit` is populated from `Indicator.unit`.
- Submission flow: User submits an activity value specifying `activity_type_id`, `reporting_period_id`, `facility_id`, and `value`. The backend looks up `ActivityType.unit` for display/aggregation.

**Developer notes**
- Model: `src/activities/models/activity_type.py` contains the save-time unit sync logic.
- Migration: `src/activities/migrations/0003_require_indicator.py` backfills legacy rows to `ACTIVITY_PLACEHOLDER` indicator before making the FK non-nullable. If you want to remap specific activity types to more meaningful indicators, update rows before running the migration.
- Tests: `src/activities/tests/test_activity_type_model.py` includes a test asserting the unit auto-sync behavior.

**Recommendations**
- Keep `ActivityType.unit` for denormalized reads and reporting performance; rely on the auto-sync to avoid divergence.
- If indicator units may change over time and you need historical fidelity, consider storing `unit` on submissions (already present) and treating `Indicator.unit` as the canonical default for future submissions.

**Contact / next steps**
- If you'd like, I can generate a CSV of `ActivityType` rows that were backfilled to `ACTIVITY_PLACEHOLDER` so you can remap them to proper indicators.
