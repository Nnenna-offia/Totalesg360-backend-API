"""Management command to calculate ESG scores."""
from django.core.management.base import BaseCommand
from django.db import transaction
import logging

from organizations.models import Organization
from submissions.models import ReportingPeriod
from esg_scoring.services.indicator_scoring import calculate_all_indicator_scores
from esg_scoring.services.pillar_scoring import calculate_all_pillar_scores
from esg_scoring.services.esg_scoring import calculate_esg_score

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """Calculate ESG scores for organizations."""
    
    help = 'Calculate ESG scores for one or more organizations'
    
    def add_arguments(self, parser):
        """Add command arguments."""
        parser.add_argument(
            '--org-id',
            type=str,
            help='Organization ID (if not specified, calculates for all active organizations)',
        )
        parser.add_argument(
            '--period-id',
            type=str,
            help='Reporting Period ID (if not specified, uses latest active period)',
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Calculate for all organizations',
        )
    
    def handle(self, *args, **options):
        """Execute command."""
        try:
            org_id = options.get('org_id')
            period_id = options.get('period_id')
            all_orgs = options.get('all')
            
            # Get organizations
            if org_id:
                orgs = [Organization.objects.get(id=org_id)]
            elif all_orgs:
                orgs = Organization.objects.filter(status='ACTIVE')
            else:
                orgs = Organization.objects.filter(status='ACTIVE')
            
            if not orgs:
                self.stdout.write(self.style.ERROR('No organizations found'))
                return
            
            # Get reporting period
            if period_id:
                period = ReportingPeriod.objects.get(id=period_id)
            else:
                period = ReportingPeriod.objects.filter(
                    is_active=True
                ).order_by('-end_date').first()
                
                if not period:
                    self.stdout.write(self.style.ERROR('No active reporting period found'))
                    return
            
            self.stdout.write(f'Calculating scores for {len(orgs)} organizations in {period.name}')
            
            # Calculate scores for each organization
            with transaction.atomic():
                for org in orgs:
                    self.stdout.write(f'  Processing {org.name}...')
                    
                    # Calculate indicator scores
                    calculate_all_indicator_scores(org, period)
                    self.stdout.write(f'    ✓ Indicator scores calculated')
                    
                    # Calculate pillar scores
                    calculate_all_pillar_scores(org, period)
                    self.stdout.write(f'    ✓ Pillar scores calculated')
                    
                    # Calculate ESG score
                    calculate_esg_score(org, period)
                    self.stdout.write(f'    ✓ ESG score calculated')
            
            self.stdout.write(self.style.SUCCESS(f'✓ Successfully calculated scores for {len(orgs)} organizations'))
            
        except Organization.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'Organization not found'))
        except ReportingPeriod.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'Reporting period not found'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error: {str(e)}'))
            logger.error(str(e), exc_info=True)
