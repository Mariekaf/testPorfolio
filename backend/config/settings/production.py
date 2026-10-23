"""Fail closed: CORE-001 is not a production deployment configuration."""
from django.core.exceptions import ImproperlyConfigured

raise ImproperlyConfigured("Production deployment is not configured in CORE-001.")
