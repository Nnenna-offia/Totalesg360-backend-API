Indicators migration and deployment notes
=====================================

Summary
-------
We removed the `source_frameworks` many-to-many field from `OrganizationIndicator`.

Background
----------
- The project previously added an M2M `source_frameworks` on `indicators.OrganizationIndicator`.
- After reviewing the model, we removed the M2M to avoid unnecessary joins and simplify tenant overrides.

Local dev
---------
- Run the test suite to verify changes: `python manage.py test indicators`.
- A migration `indicators/0003_remove_source_frameworks.py` was added and tests pass locally.

Production rollout guidance (especially if you previously faked migrations)
-----------------------------------------------------------------------
If you previously ran `python manage.py migrate indicators --fake` to mark earlier migrations applied,
take care before applying the new migration that drops the M2M table:

1. Inspect the database schema to ensure the M2M table `indicators_organizationindicator_source_frameworks` exists.
   - If it does, the migration will drop the table; ensure no production code needs that data.
2. If you had previously faked the initial indicators migrations and the M2M table exists in DB,
   run the new migration normally on a maintenance window:

```bash
python manage.py migrate indicators 0003
```

3. If you faked the initial migration and the M2M table does NOT exist (e.g., you created tables manually),
   you may need to create the M2M table or adjust the migration strategy. Preferred safe approach:

   - Restore a recent DB snapshot to a staging environment and apply migrations there.
   - If safe, run `python manage.py migrate indicators` on staging and confirm schema changes.

4. If you're unsure, contact the team lead before running migrations on production.

Post-deploy
-----------
- Confirm `OrganizationIndicator` rows are present and `is_required`/`is_active` semantics behave as expected.
- Run `python manage.py sync_org_indicators --dry-run` to preview derived OrganizationIndicator changes.

Questions
---------
If you'd like, I can produce a SQL snippet to drop the M2M table manually prior to running migrations, or
create a data-migration to migrate any stored M2M references into another table before dropping.
