from .base import *  # noqa: F403

# Keep local errors generic too: never expose DB parameters through debug pages.
DEBUG = False
CSRF_TRUSTED_ORIGINS = ["http://localhost:3000", "http://127.0.0.1:3000"]
