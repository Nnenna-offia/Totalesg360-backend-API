from django.core.management.base import BaseCommand, CommandError
from django_celery_beat.models import PeriodicTask, CrontabSchedule


class Command(BaseCommand):
    help = 'Create a daily periodic task to persist emission indicators for all locked periods.'

    def add_arguments(self, parser):
        parser.add_argument('--hour', type=int, default=2, help='Hour (0-23) to run daily')

    def handle(self, *args, **options):
        hour = options.get('hour', 2)
        schedule, created = CrontabSchedule.objects.get_or_create(minute='0', hour=str(hour), day_of_week='*', day_of_month='*', month_of_year='*')
        PeriodicTask.objects.update_or_create(
            name='persist_emission_indicators_daily',
            defaults={
                'crontab': schedule,
                'task': 'emissions.tasks.persist_emission_indicators_for_all_locked',
                'enabled': True,
            }
        )
        self.stdout.write(self.style.SUCCESS('Periodic task ensured: persist_emission_indicators_daily'))
