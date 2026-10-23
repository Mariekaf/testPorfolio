"""Shared, transactionally updated PostgreSQL limits; no in-process cache."""
import hashlib
import hmac
import math
from django.conf import settings
from django.db import transaction
from django.utils import timezone
from .models import AuthenticationLimit


class RateLimited(Exception):
    def __init__(self, seconds):
        self.seconds = max(1, seconds)


def consume(scope, identity):
    maximum, window = settings.AUTH_RATE_LIMITS[scope]
    digest = hmac.new(settings.SECRET_KEY.encode(), (scope+':'+identity).encode(), hashlib.sha256).hexdigest()
    now = timezone.now()
    with transaction.atomic():
        bucket, _ = AuthenticationLimit.objects.select_for_update().get_or_create(key=digest, defaults={'window_start': now})
        elapsed = (now-bucket.window_start).total_seconds()
        if elapsed >= window:
            bucket.attempts, bucket.window_start = 0, now
        elif bucket.attempts >= maximum:
            raise RateLimited(math.ceil(window-elapsed))
        bucket.attempts += 1
        bucket.save(update_fields=['attempts','window_start'])


def limit_request(request, scope, email=None):
    # Never trust a client-supplied X-Forwarded-For. Public proxy policy is deferred.
    consume(scope+'_ip', request.META.get('REMOTE_ADDR','unknown'))
    if email is not None:
        consume(scope+'_email', email)
