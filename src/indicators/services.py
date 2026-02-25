import threading
from typing import Tuple, Iterable, Dict
from django.db import transaction

from organizations.models import Organization, OrganizationFramework
from indicators.models import Indicator, FrameworkIndicator, OrganizationIndicator


def _run_in_background(fn, *args, **kwargs):
    t = threading.Thread(target=fn, args=args, kwargs=kwargs, daemon=True)
    t.start()


def sync_org_indicators_for_org(org: Organization) -> Tuple[int, int, int]:
    """Sync/derive OrganizationIndicator rows for a single organization.

    Returns (created, updated, skipped)
    """
    # Get enabled frameworks for org
    enabled_fw_ids = list(OrganizationFramework.objects.filter(organization=org, is_enabled=True).values_list('framework_id', flat=True))
    if not enabled_fw_ids:
        return 0, 0, 0

    fw_ind_qs = FrameworkIndicator.objects.filter(framework_id__in=enabled_fw_ids).select_related('indicator')

    indicator_map: Dict[str, Dict] = {}
    for fi in fw_ind_qs:
        ind_id = str(fi.indicator_id)
        entry = indicator_map.setdefault(ind_id, {"indicator": fi.indicator, "frameworks": set(), "required": False})
        entry["frameworks"].add(fi.framework_id)
        if fi.is_required:
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
            changed = False
            if not org_ind.is_active:
                org_ind.is_active = True
                changed = True
            to_update.append((org_ind, frameworks))
        else:
            oi = OrganizationIndicator(organization=org, indicator=indicator, is_required=None, is_active=True)
            to_create.append((oi, frameworks))

    created = 0
    updated = 0
    with transaction.atomic():
        if to_create:
            OrganizationIndicator.objects.bulk_create([t[0] for t in to_create])
            created = len(to_create)
            # No more tracking of source_frameworks; created OrganizationIndicator rows are persisted
            # with `is_required=None` to indicate inheritance from frameworks.
            for oi, frameworks in to_create:
                OrganizationIndicator.objects.get(organization=oi.organization, indicator=oi.indicator)

        for oi, frameworks in to_update:
            oi.save()
            updated += 1

    return created, updated, skipped


def schedule_sync_for_org(org: Organization):
    # run after transaction commit to ensure data is consistent
    transaction.on_commit(lambda: _run_in_background(sync_org_indicators_for_org, org))
