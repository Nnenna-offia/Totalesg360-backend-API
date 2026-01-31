#=========================================================================
# Utility functions for loading environment variables and database config
#=========================================================================

from pathlib import Path
import os
from typing import Union
from dotenv import load_dotenv
from django.core.exceptions import ImproperlyConfigured


def load_env_file(base_dir: Union[str, Path], filename: str, override: bool = True) -> None:
    """Load an env file located at base_dir/filename."""
    load_dotenv(str(Path(base_dir) / filename), override=override)


def get_database_config(_: Union[str, Path] = None):
    """Return a DATABASES dict driven by env vars.

    This project requires an explicit `DB_ENGINE` in the environment (no sqlite
    fallback). If `DB_ENGINE` is not set an `ImproperlyConfigured` is raised
    with instructions to set the DB_* environment variables.
    """
    engine = os.getenv("DB_ENGINE", "").strip()
    if not engine:
        raise ImproperlyConfigured(
            "DB_ENGINE is not set. Configure your database via env vars: "
            "DB_ENGINE, DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT."
        )

    port_val = os.getenv("DB_PORT", "").strip()
    try:
        port = int(port_val) if port_val else None
    except ValueError:
        port = None

    return {
        "default": {
            "ENGINE": engine,
            "NAME": os.getenv("DB_NAME", ""),
            "USER": os.getenv("DB_USER", ""),
            "PASSWORD": os.getenv("DB_PASSWORD", ""),
            "HOST": os.getenv("DB_HOST", ""),
            "PORT": port,
        }
    }
