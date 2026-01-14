from pathlib import Path
import os
from typing import Union
from dotenv import load_dotenv


def load_env_file(base_dir: Union[str, Path], filename: str, override: bool = True) -> None:
    """Load an env file located at base_dir/filename."""
    load_dotenv(str(Path(base_dir) / filename), override=override)


def get_database_config(default_sqlite_path: Union[str, Path]):
    """Return a DATABASES dict driven by env vars or fall back to sqlite."""
    engine = os.getenv("DB_ENGINE", "").strip()
    if engine:
        port_val = os.getenv("DB_PORT", "").strip()
        try:
            port = int(port_val) if port_val else None
        except ValueError:
            port = None
        return {
            "default": {
                "ENGINE": engine,
                "NAME": os.getenv("DB_NAME", "app"),
                "USER": os.getenv("DB_USER", "postgres"),
                "PASSWORD": os.getenv("DB_PASSWORD", "postgres"),
                "HOST": os.getenv("DB_HOST", "localhost"),
                "PORT": port,
            }
        }

    return {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": str(default_sqlite_path),
        }
    }
