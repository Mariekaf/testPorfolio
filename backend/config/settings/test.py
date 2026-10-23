"""Dedicated test role may create/drop test databases, runtime role may not."""
from .base import *  # noqa: F403

DATABASES["default"].update(USER=CONFIG["database"]["test_user"], PASSWORD=CONFIG["database"]["test_password"])
DATABASES["default"]["TEST"] = {"NAME": "test_" + CONFIG["database"]["name"]}

TEST_RUNNER = "config.test_runner.PostgreSQLTestRunner"
