from typing import Iterable, Dict, Set
from django.core.management.base import BaseCommand
from django.db import transaction

from organizations.models import Organization, OrganizationFramework
from indicators.models import Indicator, OrganizationIndicator
from compliance.models import IndicatorFrameworkMapping


class Command(BaseCommand):
    help = "Sync/derive OrganizationIndicator rows from enabled OrganizationFramework entries."

    def add_arguments(self, parser):
        parser.add_argument("--org", dest="org_id", help="Limit sync to a single organization id or slug")
        parser.add_argument("--dry-run", action="store_true", dest="dry_run", help="Show changes but do not persist")
        parser.add_argument("--commit", action="store_true", dest="commit", help="Persist changes (same as not using --dry-run)")

    def handle(self, *args, **options):
        org_id = options.get("org_id")
        dry_run = options.get("dry_run", False)

        if org_id:
            orgs = Organization.objects.filter(id=org_id) if self._looks_like_uuid(org_id) else Organization.objects.filter(name__iexact=org_id)
        else:
            # Only organizations with at least one enabled framework
            orgs = Organization.objects.filter(organization_assignments__is_enabled=True).distinct()

        total_created = 0
        total_updated = 0
        total_skipped = 0

        from indicators.services import sync_org_indicators_for_org

        for org in orgs.select_related():
            self.stdout.write(f"Processing org: {org.name} ({org.id})")
            if dry_run:
                # call service but do not persist (service always persists) -> emulate via dry-run path
                created, updated, skipped = self._process_org(org, dry_run=True)
            else:
                created, updated, skipped = sync_org_indicators_for_org(org)
            total_created += created
            total_updated += updated
            total_skipped += skipped

        self.stdout.write("")
        self.stdout.write(f"Summary: created={total_created} updated={total_updated} skipped={total_skipped}")

    def _process_org(self, org: Organization, dry_run: bool = False):
        # dry-run path mirrors service behavior but does not persist
        enabled_fw_ids = list(OrganizationFramework.objects.filter(organization=org, is_enabled=True).values_list('framework_id', flat=True))
        if not enabled_fw_ids:
            self.stdout.write("  no enabled frameworks, skipping")
            return 0, 0, 0

        mappings_qs = (
            IndicatorFrameworkMapping.objects
            .filter(requirement__framework__in=enabled_fw_ids, is_active=True)
            .select_related('indicator', 'requirement')
        )

        indicator_map: Dict[str, Dict] = {}
        for mapping in mappings_qs:
            ind_id = str(mapping.indicator_id)
            entry = indicator_map.setdefault(ind_id, {"indicator": mapping.indicator, "frameworks": set(), "required": False})
            entry["frameworks"].add(mapping.requirement.framework_id)
            if mapping.requirement.is_mandatory:
                entry["required"] = True

        indicator_ids = [k for k in indicator_map.keys()]
        existing_qs = OrganizationIndicator.objects.filter(organization=org, indicator_id__in=indicator_ids).select_related('indicator')
        existing_map = {str(o.indicator_id): o for o in existing_qs}

        to_create = []
        to_update = []
        skipped = 0

        for ind_id, meta in indicator_map.items():
            indicator = meta['indicator']
            frameworks = meta['frameworks']

            org_ind = existing_map.get(ind_id)
            if org_ind:
                if org_ind.is_required is not None:
                    skipped += 1
                    continue
                to_update.append((org_ind, frameworks))
            else:
                to_create.append((indicator, frameworks))

        self.stdout.write(f"  dry-run: would create {len(to_create)} org indicators, update {len(to_update)}")
        return len(to_create), len(to_update), skipped

    @staticmethod
    def _looks_like_uuid(val: str) -> bool:
        return len(val) == 36 and val.count('-') == 4
