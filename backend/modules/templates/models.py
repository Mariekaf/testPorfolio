import uuid
from django.conf import settings
from django.db import models

class PortfolioDesign(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    portfolio = models.OneToOneField('portfolios.Portfolio', on_delete=models.PROTECT, related_name='design')
    schema_version = models.PositiveSmallIntegerField(default=1, editable=False)
    composition = models.JSONField()
    content = models.JSONField()
    presentation = models.JSONField()
    customization = models.JSONField()
    experience = models.JSONField(null=True, default=None)
    source_digest = models.CharField(max_length=64, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.CheckConstraint(condition=models.Q(schema_version=1), name='tpl_design_schema_v1'),
            models.CheckConstraint(condition=models.Q(experience__isnull=True), name='tpl_no_experience_v1'),
            models.CheckConstraint(condition=models.Q(source_digest__regex=r'^[0-9a-f]{64}$'), name='tpl_source_digest_valid'),
        ]

class TemplateCreationRequest(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    account = models.ForeignKey('accounts.Account', on_delete=models.PROTECT)
    key = models.UUIDField()
    request_digest = models.CharField(max_length=64)
    portfolio = models.ForeignKey('portfolios.Portfolio', on_delete=models.PROTECT)
    response_body = models.JSONField()
    response_etag = models.CharField(max_length=150)
    completed_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(db_index=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['user','account','key'], name='tpl_creation_key_unique')]
