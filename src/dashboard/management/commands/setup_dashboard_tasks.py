from django.core.management.base import BaseCommand
from django_celery_beat.models import PeriodicTask, CrontabSchedule
import json


class Command(BaseCommand):
    help = 'Create periodic Celery Beat task to run dashboard.compute_snapshots daily at 02:00'

    def handle(self, *args, **options):
        schedule, _ = CrontabSchedule.objects.get_or_create(minute='0', hour='2', day_of_week='*', day_of_month='*', month_of_year='*')
        task_name = 'dashboard.compute_snapshots'
        PeriodicTask.objects.update_or_create(
            name='dashboard-compute-daily',
            defaults={
                'crontab': schedule,
                'task': task_name,
                'enabled': True,
                'kwargs': json.dumps({}),
            }
        )
        self.stdout.write(self.style.SUCCESS('Registered periodic task dashboard.compute_snapshots'))
