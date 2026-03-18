Worker startup: waiting for DB tables
===================================

What changed
------------

The container entrypoint was updated to call Django's `manage.py wait_for_tables`
before starting Celery worker/beat processes. This prevents Celery from executing
periodic tasks (like `dashboard.cleanup_old_snapshots`) before database migrations
have been applied and the snapshot tables exist.

How it works
------------

- The management command `wait_for_tables` lives at `src/dashboard/management/commands/wait_for_tables.py`.
- By default it waits for these tables:
  - `dashboard_dashboardsnapshot`
  - `dashboard_targetsnapshot`
  - `dashboard_emissionsnapshot`
  - `dashboard_indicatorsnapshot`
  - `dashboard_compliancesnapshot`
- The entrypoint runs `python manage.py wait_for_tables` when the container is
  invoked to start Celery.

Tuning
------

- Timeout: pass `--timeout` to `manage.py wait_for_tables` to change how long to wait (seconds).
- Poll interval: pass `--interval` to change how often it checks for tables (seconds).
- Custom tables: pass `--tables "table1,table2"` to wait for a custom list.

Examples
--------

Run the command manually with a 120s timeout:

```bash
./manage.py wait_for_tables --timeout 120
```

Or wait for specific tables:

```bash
./manage.py wait_for_tables --tables "auth_user,myapp_mymodel" --timeout 60
```

Notes
-----

- The command exits with non-zero status if the timeout is reached. The entrypoint
  uses `|| true` to avoid blocking container startup in environments where you prefer
  to handle ordering externally (e.g., Kubernetes initContainers).
- For Kubernetes, prefer an initContainer that runs `./manage.py migrate` before
  starting workers/beat; the wait helper is primarily for simple docker-compose
  or non-orchestrated deployments.
