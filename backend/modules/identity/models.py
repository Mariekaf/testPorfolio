"""Authentication only. No accounts, portfolios or collaboration models."""
import uuid
from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.contrib.sessions.models import Session
from django.db import models
from django.db.models.functions import Lower

from .managers import UserManager, normalize_identity_email


class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    username = None
    email = models.EmailField(max_length=254, unique=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']
    objects = UserManager()

    class Meta:
        constraints = [models.UniqueConstraint(Lower('email'), name='identity_user_email_ci_unique')]

    def save(self, *args, **kwargs):
        self.email = normalize_identity_email(self.email)
        super().save(*args, **kwargs)


class AuthSession(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    session = models.OneToOneField(Session, on_delete=models.CASCADE, primary_key=True)
    created_at = models.DateTimeField(auto_now_add=True)


class AuthenticationLimit(models.Model):
    # HMAC keys, never raw IP addresses or email addresses.
    key = models.CharField(max_length=64, primary_key=True)
    attempts = models.PositiveIntegerField(default=0)
    window_start = models.DateTimeField()
