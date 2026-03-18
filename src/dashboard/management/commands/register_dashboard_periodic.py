from django.core.management.base import BaseCommand
from django_celery_beat.models import PeriodicTask, IntervalSchedule
import json
from django.conf import settings


class Command(BaseCommand):
    help = 'Register dashboard.populate_snapshots as a nightly Celery Beat task'

    def handle(self, *args, **options):
        # daily at midnight schedule via IntervalSchedule every 24 hours
        schedule, _ = IntervalSchedule.objects.get_or_create(every=24, period=IntervalSchedule.HOURS)
        task_name = 'dashboard.populate_snapshots'
        PeriodicTask.objects.update_or_create(
            name='dashboard-populate-nightly',
            defaults={
                'interval': schedule,
                'task': task_name,
                'enabled': True,
                'kwargs': json.dumps({}),
            }
        )
        # Register cleanup task (daily) using retention from settings
        try:
            cleanup_schedule, _ = IntervalSchedule.objects.get_or_create(every=1, period=IntervalSchedule.DAYS)
            cleanup_task = 'dashboard.cleanup_old_snapshots'
            kwargs = json.dumps({'retention_days': int(getattr(settings, 'DASHBOARD_SNAPSHOT_RETENTION_DAYS', 365))})
            PeriodicTask.objects.update_or_create(
                name='dashboard-cleanup-daily',
                defaults={
                    'interval': cleanup_schedule,
                    'task': cleanup_task,
                    'enabled': True,
                    'kwargs': kwargs,
                }
            )
        except Exception:
            pass
        self.stdout.write(self.style.SUCCESS('Registered periodic task dashboard.populate_snapshots'))
