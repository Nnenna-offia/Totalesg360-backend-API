from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from datetime import timedelta
from dashboard.tasks import populate_dashboard_snapshots


class Command(BaseCommand):
    help = 'Backfill dashboard snapshots for the past N days (creates one snapshot per day)'

    def add_arguments(self, parser):
        parser.add_argument('--days', type=int, default=30, help='Number of past days to backfill (default: 30)')
        parser.add_argument('--chunk-size', type=int, default=100, help='Chunk size passed to populate task')
        parser.add_argument('--pause-seconds', type=float, default=0.0, help='Pause between batches for the populate task')

    def handle(self, *args, **options):
        days = options.get('days')
        if days <= 0:
            raise CommandError('days must be a positive integer')

        chunk_size = options.get('chunk_size')
        pause_seconds = options.get('pause_seconds')

        now = timezone.now()
        created_total = 0
        for i in range(1, days + 1):
            snap_date = now - timedelta(days=i)
            self.stdout.write(f'Backfilling snapshot for {snap_date.date()}')
            # call the populate task synchronously for historical date
            res = populate_dashboard_snapshots(snapshot_date=snap_date, chunk_size=chunk_size, pause_seconds=pause_seconds)
            # res may be AsyncResult or dict depending on execution; try to count
            try:
                created_total += res.get('created_orgs', 0) if isinstance(res, dict) else 0
            except Exception:
                pass

        self.stdout.write(self.style.SUCCESS(f'Backfill complete (requested days={days})'))
