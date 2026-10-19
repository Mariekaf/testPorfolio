import os
from pathlib import Path

from config.environment import load_configuration

BASE_DIR = Path(__file__).resolve().parents[2]
CONFIG = load_configuration()
SECRET_KEY = CONFIG["secret_key"]
DEBUG = False
ALLOWED_HOSTS = ["127.0.0.1", "localhost"]
INSTALLED_APPS = [
    "django.contrib.auth", "django.contrib.contenttypes", "django.contrib.sessions",
    "modules.templates.apps.TemplatesConfig",
    "rest_framework", "modules.identity.apps.IdentityConfig", "modules.portfolios.apps.PortfoliosConfig", "modules.accounts.apps.AccountsConfig",
]
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "modules.templates.middleware.DesignBodyLimit",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]
ROOT_URLCONF = "config.urls"
SAAS_HERO_TRANSITIONS_ENABLED = os.environ.get('SAAS_HERO_TRANSITIONS_ENABLED', '0') == '1'
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"
AUTH_USER_MODEL = "identity.User"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
USE_TZ = True
TIME_ZONE = "UTC"
LANGUAGE_CODE = "fr-fr"
APPEND_SLASH = False
SESSION_COOKIE_AGE = 8 * 3600
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Strict"
CSRF_COOKIE_SAMESITE = "Strict"
X_FRAME_OPTIONS = "DENY"
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": ["rest_framework.authentication.SessionAuthentication"],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
}
_db = CONFIG["database"]
DATABASES = {"default": {
    "ENGINE": "django.db.backends.postgresql",
    "HOST": _db["host"], "PORT": str(_db["port"]), "NAME": _db["name"],
    "USER": _db["runtime_user"], "PASSWORD": _db["runtime_password"],
    "CONN_MAX_AGE": 0,
    "OPTIONS": {"connect_timeout": 3, "options": "-c statement_timeout=3000"},
}}

# AUTH-001: isolated cookies and explicit, bounded session lifetime.
def positive_seconds(name, default):
    value = int(os.environ.get(name, default))
    if not 60 <= value <= 86400:
        raise ValueError(name + " must be between 60 and 86400")
    return value

SESSION_COOKIE_NAME = "portfolio_saas_session"
CSRF_COOKIE_NAME = "portfolio_saas_csrf"
CSRF_COOKIE_HTTPONLY = True
SESSION_COOKIE_AGE = positive_seconds("SAAS_SESSION_SECONDS", 28800)
PASSWORD_RESET_TIMEOUT = positive_seconds("SAAS_RESET_SECONDS", 1800)
SESSION_COOKIE_SECURE = os.environ.get("SAAS_HTTPS", "0") == "1"
CSRF_COOKIE_SECURE = SESSION_COOKIE_SECURE
CSRF_FAILURE_VIEW = "modules.identity.views.csrf_failure"
STUDIO_ORIGIN = os.environ.get("SAAS_STUDIO_ORIGIN", "http://127.0.0.1:3000").rstrip("/")
from urllib.parse import urlsplit
_origin = urlsplit(STUDIO_ORIGIN)
if (_origin.username or _origin.password or _origin.query or _origin.fragment
        or _origin.path or _origin.scheme not in {"http", "https"}
        or not _origin.hostname or (_origin.scheme == "http" and
        (_origin.hostname not in {"localhost", "127.0.0.1"} or SESSION_COOKIE_SECURE))):
    raise ValueError("Invalid SAAS_STUDIO_ORIGIN")
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator", "OPTIONS": {"min_length": 12}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]
AUTH_RATE_LIMITS = {
    "register_ip": (10, 300), "login_ip": (20, 300), "login_email": (8, 300),
    "reset_ip": (10, 300), "reset_email": (3, 900), "confirm_ip": (20, 300),
}
DEFAULT_FROM_EMAIL = os.environ.get("SAAS_EMAIL_FROM", "no-reply@example.test")
EMAIL_BACKEND = "modules.identity.mailbox.PrivateMailboxBackend"
EMAIL_FILE_PATH = Path(os.environ.get("SAAS_MAILBOX_PATH", BASE_DIR.parent / "infra" / "mailbox"))
DATA_UPLOAD_MAX_MEMORY_SIZE = 16384
if os.environ.get("SAAS_EMAIL_HOST"):
    EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
    EMAIL_HOST = os.environ["SAAS_EMAIL_HOST"]
    EMAIL_PORT = int(os.environ.get("SAAS_EMAIL_PORT", "587"))
    EMAIL_HOST_USER = os.environ.get("SAAS_EMAIL_USER", "")
    EMAIL_HOST_PASSWORD = os.environ.get("SAAS_EMAIL_PASSWORD", "")
    EMAIL_USE_TLS = True
    EMAIL_TIMEOUT = 10
