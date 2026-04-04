from django.core.management.base import BaseCommand

from activities.models.scope import Scope
from indicators.models.indicator import Indicator
from activities.models.activity_type import ActivityType


class Command(BaseCommand):
    help = "Seed sample scopes, indicators and activity types for Activities UI"

    def handle(self, *args, **options):
        # Scopes
        scopes = {
            'emissions': 'Emissions',
            'social': 'Social',
            'governance': 'Governance'
        }
        for code, name in scopes.items():
            Scope.objects.get_or_create(code=code, defaults={'name': name})

        # Indicators (simple examples)
        ind_defs = [
            {'code': 'GHG-CO2', 'name': 'Total GHG Emissions', 'unit': 'tonnes', 'collection_method': Indicator.CollectionMethod.ACTIVITY, 'data_type': Indicator.DataType.NUMBER},
            {'code': 'WASTE-TOTAL', 'name': 'Total Waste', 'unit': 'tonnes', 'collection_method': Indicator.CollectionMethod.ACTIVITY, 'data_type': Indicator.DataType.NUMBER},
            {'code': 'EMP-COUNT', 'name': 'Total Employees', 'unit': 'count', 'collection_method': Indicator.CollectionMethod.ACTIVITY, 'data_type': Indicator.DataType.NUMBER},
            {'code': 'FEMALE-PCT', 'name': 'Female Workforce %', 'unit': 'percent', 'collection_method': Indicator.CollectionMethod.ACTIVITY, 'data_type': Indicator.DataType.PERCENT},
            {'code': 'BOARD-SEPARATION', 'name': 'Chair/CEO Separation', 'unit': '', 'collection_method': Indicator.CollectionMethod.ACTIVITY, 'data_type': Indicator.DataType.BOOLEAN},
        ]

        created_inds = {}
        for d in ind_defs:
            ind, _ = Indicator.objects.get_or_create(code=d['code'], defaults={
                'name': d['name'],
                'unit': d['unit'],
                'collection_method': d['collection_method'],
                'data_type': d['data_type'],
                'pillar': Indicator.Pillar.ENVIRONMENTAL,
            })
            created_inds[d['code']] = ind

        # Activity types examples
        examples = [
            # Environmental
            {'name': 'Scope 1 - CO2 Emissions', 'indicator_code': 'GHG-CO2', 'scope_code': 'emissions', 'data_type': 'number'},
            {'name': 'Scope 2 - Energy Indirect', 'indicator_code': 'GHG-CO2', 'scope_code': 'emissions', 'data_type': 'number'},
            {'name': 'Waste Management - Total Waste', 'indicator_code': 'WASTE-TOTAL', 'scope_code': 'emissions', 'data_type': 'number'},
            # Social
            {'name': 'Total Employees', 'indicator_code': 'EMP-COUNT', 'scope_code': 'social', 'data_type': 'number'},
            {'name': 'Female Workforce %', 'indicator_code': 'FEMALE-PCT', 'scope_code': 'social', 'data_type': 'percentage'},
            # Governance
            {'name': 'Chair/CEO Separation', 'indicator_code': 'BOARD-SEPARATION', 'scope_code': 'governance', 'data_type': 'boolean'},
        ]

        for ex in examples:
            scope = Scope.objects.get(code=ex['scope_code'])
            indicator = created_inds.get(ex['indicator_code'])
            ActivityType.objects.get_or_create(
                name=ex['name'],
                defaults={
                    'description': '',
                    'unit': indicator.unit if indicator and indicator.unit else '',
                    'scope': scope,
                    # category removed; grouping is handled by Indicator -> ActivityType
                    'display_order': 0,
                    'data_type': ex.get('data_type', 'number'),
                    'requires_evidence': False,
                    'is_required': False,
                    'is_active': True,
                    'indicator': indicator,
                }
            )

        self.stdout.write(self.style.SUCCESS('Seeded sample scopes, indicators and activity types.'))
