import uuid
from django.conf import settings
from django.db import models

class Portfolio(models.Model):
    class Type(models.TextChoices):
        PERSONAL = "personal", "Personnel"
        PROFESSIONAL = "professional", "Professionnel"
        BUSINESS = "business", "Entreprise"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="portfolios")
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=110, unique=True)
    description = models.CharField(max_length=500, blank=True)
    portfolio_type = models.CharField(max_length=20, choices=Type.choices, default=Type.PERSONAL)
    status = models.CharField(max_length=16, default="draft", editable=False)
    visibility = models.CharField(max_length=16, default="private", editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True, db_index=True)

    class Meta:
        ordering = ["-updated_at", "-created_at"]
        constraints = [
            models.CheckConstraint(condition=models.Q(status="draft"), name="port001_draft_only"),
            models.CheckConstraint(condition=models.Q(visibility="private"), name="port001_private_only"),
        ]
