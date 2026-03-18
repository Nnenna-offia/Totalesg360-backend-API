from django.core.management.base import BaseCommand, CommandError
from organizations.models import Organization
from submissions.models import ReportingPeriod
from emissions.services.persist_indicators import persist_emission_indicators


class Command(BaseCommand):
    help = 'Persist emission-derived indicators for an organization and reporting period.'

    def add_arguments(self, parser):
        parser.add_argument('--org-id', dest='org_id', required=True)
        parser.add_argument('--period-id', dest='period_id', required=True)

    def handle(self, *args, **options):
        org_id = options['org_id']
        period_id = options['period_id']
        try:
            org = Organization.objects.get(id=org_id)
        except Organization.DoesNotExist:
            raise CommandError('Organization not found')

        try:
            period = ReportingPeriod.objects.get(id=period_id, organization=org)
        except ReportingPeriod.DoesNotExist:
            raise CommandError('ReportingPeriod not found for organization')

        res = persist_emission_indicators(org, period, by_user=None, submit=True)
        self.stdout.write(self.style.SUCCESS(f'Persisted indicators: {list(res.keys())}'))
