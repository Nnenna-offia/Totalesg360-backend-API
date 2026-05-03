import threading
import logging
from typing import Tuple, Dict
from django.db import transaction

from organizations.models import Organization, OrganizationFramework
from indicators.models import Indicator, OrganizationIndicator
from compliance.models import IndicatorFrameworkMapping


logger = logging.getLogger(__name__)


def _run_in_background(fn, *args, **kwargs):
    def _runner():
        try:
            fn(*args, **kwargs)
        except Exception:
            logger.exception("Organization indicator sync failed in background thread")

    t = threading.Thread(target=_runner, daemon=True)
    t.start()


def sync_org_indicators_for_org(org: Organization) -> Tuple[int, int, int]:
    """Sync/derive OrganizationIndicator rows for a single organization.

    Returns (created, updated, skipped)
    """
    # Get enabled frameworks for org
    enabled_fw_ids = list(OrganizationFramework.objects.filter(organization=org, is_enabled=True).values_list('framework_id', flat=True))
    if not enabled_fw_ids:
        logger.info(
            "Organization indicator sync skipped: no enabled frameworks for org=%s",
            org.id,
        )
        return 0, 0, 0

    logger.info(
        "Organization indicator sync started for org=%s with enabled_frameworks=%s",
        org.id,
        len(enabled_fw_ids),
    )

    # Get all active mappings for enabled frameworks
    mappings_qs = (
        IndicatorFrameworkMapping.objects
        .filter(
            requirement__framework__in=enabled_fw_ids,
            is_active=True
        )
        .select_related('indicator', 'requirement')
    )

    indicator_map: Dict[str, Dict] = {}
    for mapping in mappings_qs:
        ind_id = str(mapping.indicator_id)
        entry = indicator_map.setdefault(
            ind_id,
            {"indicator": mapping.indicator, "frameworks": set(), "required": False}
        )
        entry["frameworks"].add(mapping.requirement.framework_id)
        # Indicator is required if any mapping's requirement is mandatory
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
            # Ensure created rows are present in DB (no-op get just to be explicit)
            for oi, frameworks in to_create:
                OrganizationIndicator.objects.get(organization=oi.organization, indicator=oi.indicator)

        for oi, frameworks in to_update:
            oi.save()
            updated += 1

    logger.info(
        "Organization indicator sync completed for org=%s (created=%s, updated=%s, skipped=%s)",
        org.id,
        created,
        updated,
        skipped,
    )

    return created, updated, skipped


def schedule_sync_for_org(org: Organization):
    # run after transaction commit to ensure data is consistent
    logger.info("Organization indicator sync queued for org=%s", org.id)

    def _enqueue_sync():
        logger.info("Organization indicator sync dispatching background thread for org=%s", org.id)
        _run_in_background(sync_org_indicators_for_org, org)

    transaction.on_commit(_enqueue_sync)

