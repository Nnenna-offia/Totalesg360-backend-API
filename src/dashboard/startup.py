import time
from typing import List
from django.db import connection
import logging

logger = logging.getLogger(__name__)


def wait_for_tables(tables: List[str], timeout: int = 300, interval: float = 1.0) -> bool:
    """Wait until all `tables` exist in the configured database.

    Returns True if tables exist before timeout, False otherwise.
    This is intended for worker startup to avoid running periodic tasks
    against an unmigrated database.
    """
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with connection.cursor() as cursor:
                existing = set(connection.introspection.table_names())
        except Exception as exc:
            logger.debug('DB not ready yet: %s', exc)
            existing = set()

        missing = [t for t in tables if t not in existing]
        if not missing:
            return True

        logger.info('Waiting for tables to exist: %s (missing: %s)', tables, missing)
        time.sleep(interval)

    logger.warning('Timed out waiting for tables: %s', tables)
    return False
