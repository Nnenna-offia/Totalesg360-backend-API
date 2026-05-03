# Data Population Scripts

This directory contains Django management commands and helper scripts for data population and fixtures.

## Quick Start: List Organizations

Before running any population commands, check available organizations:

```bash
python ./scripts/check_orgs.py
```

This will show all organization IDs and names. Use these IDs/names with the populate commands below.

## Management Commands

### populate_activities

Create `ActivityType` entries and optionally submit `ActivitySubmission` rows.

**Usage:**
```bash
./manage.py populate_activities --org-id "2010405f-f330-44c9-a513-00929c3d4d9b" --count 10
./manage.py populate_activities --org-id "Bytgates" --count 5 --submit --reporting-period-id 1 --user-id 2 --value-min 10 --value-max 100
./manage.py populate_activities --org-id "ACME" --count 20 --dry-run --fixtures tmp/activities.json
./manage.py loaddata tmp/activities.json
```

**Key Arguments:**
- `--org-id` (required): organization ID (UUID or name substring match)
- `--count` (default 10): number of activity types to create
- `--activity-prefix` (default "AutoActivity"): prefix for activity type names
- `--unit` (default "kgCO2"): unit of measurement
- `--submit`: also create ActivitySubmission rows
- `--reporting-period-id`: required if `--submit` is set
- `--user-id` / `--username`: required if `--submit` is set
- `--value-min` / `--value-max` (default 1.0–100.0): range for random values
- `--dry-run`: don't write to DB
- `--fixtures PATH`: write Django JSON fixtures to file
- `--seed N`: use fixed random seed for reproducibility

### populate_indicators

Create `Indicator` entries and optionally map them to organizations/frameworks.

**Usage:**
```bash
./manage.py populate_indicators --org-id "2010405f-f330-44c9-a513-00929c3d4d9b" --count 10
./manage.py populate_indicators --org-id "ACME" --count 5 --pillar Environmental --framework-id 1
./manage.py populate_indicators --org-id "Bytgates" --count 20 --dry-run --fixtures tmp/indicators.json
./manage.py loaddata tmp/indicators.json
```

**Key Arguments:**
- `--org-id` (required): organization ID (UUID or name substring match)
- `--count` (default 10): number of indicators to create
- `--pillar` (default "Environmental"): one of ENV/Environmental, SOC/Social, GOV/Governance
- `--data-type` (default "numeric"): data type for indicators
- `--unit` (default "kg"): unit of measurement
- `--framework-id` / `--framework-code`: optional RegulatoryFramework to map to
- `--create-mappings`: create `OrganizationIndicator` mappings
- `--dry-run`: don't write to DB
- `--fixtures PATH`: write Django JSON fixtures to file
- `--seed N`: use fixed random seed for reproducibility

## Loading Fixtures

Once fixtures are generated, load them into your database:

```bash
./manage.py populate_activities --org-id "Bytgates" --count 5 --fixtures activities.json
./manage.py loaddata activities.json
```

Or load from an existing file without regenerating:

```bash
./manage.py loaddata activities.json indicators.json
```

**Note:** Fixtures include timestamps (`created_at`, `updated_at`) so they load correctly into models with timestamp requirements.

## Script Deprecation

The standalone scripts `populate_activities.py` and `populate_indicators.py` are deprecated. They require manual Django setup and don't integrate with the framework's error handling. Use the management commands above instead.
