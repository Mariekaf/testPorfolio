"""Load the SaaS configuration only. Never opens legacy .local data."""
import json
import os
import sys
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG = ROOT / "infra/env/development.local.json"


def load_configuration():
    if sys.version_info[:2] != (3, 13):
        raise ImproperlyConfigured("The SaaS foundations require Python 3.13. Legacy CMS runtime is unchanged.")
    path = Path(os.environ.get("SAAS_CONFIG_FILE", DEFAULT_CONFIG))
    if not path.is_file():
        raise ImproperlyConfigured("SaaS configuration missing. Run Initialize-Development.ps1 first.")
    try:
        config = json.loads(path.read_text(encoding="utf-8-sig"))
        required = ["secret_key", "database", "database_mode"]
        if not isinstance(config, dict) or any(key not in config for key in required):
            raise ValueError
        db = config["database"]
        for key in ["host", "port", "name", "runtime_user", "runtime_password", "migration_user", "migration_password", "test_user", "test_password"]:
            if not db.get(key):
                raise ValueError
        if config["database_mode"] not in ("native", "docker") or len(config["secret_key"]) < 50:
            raise ValueError
        int(db["port"])
    except (ValueError, TypeError, AttributeError):
        raise ImproperlyConfigured("Invalid SaaS configuration; no values are logged.") from None
    return config
