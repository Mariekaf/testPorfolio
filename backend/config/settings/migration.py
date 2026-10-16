"""Explicit local DDL connection; never used by the runtime server."""
from .base import *  # noqa: F403

DATABASES["default"].update(USER=CONFIG["database"]["migration_user"], PASSWORD=CONFIG["database"]["migration_password"])
