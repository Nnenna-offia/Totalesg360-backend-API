from django.core.management.base import BaseCommand
from dashboard.startup import wait_for_tables


class Command(BaseCommand):
    help = 'Wait until specified DB tables exist (useful for worker startup)'

    def add_arguments(self, parser):
        parser.add_argument('--tables', type=str, help='Comma-separated list of tables to wait for')
        parser.add_argument('--timeout', type=int, default=300, help='Timeout in seconds')
        parser.add_argument('--interval', type=float, default=1.0, help='Poll interval in seconds')

    def handle(self, *args, **options):
        tables_arg = options.get('tables')
        if tables_arg:
            tables = [t.strip() for t in tables_arg.split(',') if t.strip()]
        else:
            # sensible defaults for dashboard snapshot tables
            tables = [
                'dashboard_dashboardsnapshot',
                'dashboard_targetsnapshot',
                'dashboard_emissionsnapshot',
                'dashboard_indicatorsnapshot',
                'dashboard_compliancesnapshot',
            ]

        timeout = options.get('timeout')
        interval = options.get('interval')
        ok = wait_for_tables(tables, timeout=timeout, interval=interval)
        if not ok:
            self.stderr.write(self.style.WARNING('Timed out waiting for tables: %s' % tables))
            raise SystemExit(1)
        self.stdout.write(self.style.SUCCESS('All tables present: %s' % (tables,)))
