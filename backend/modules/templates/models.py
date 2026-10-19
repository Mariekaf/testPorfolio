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
            models.CheckConstraint(condition=models.Q(schema_version__in=[1, 2]), name='tpl_design_schema_v1_v2'),
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


class DesignTransition(models.Model):
    """Append-only recovery and exact idempotency record; owner via design.portfolio."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    design = models.ForeignKey(PortfolioDesign, on_delete=models.PROTECT, related_name='transitions')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    key = models.UUIDField()
    action = models.CharField(max_length=12)
    converter_version = models.CharField(max_length=30, default='1.0.0', editable=False)
    request_digest = models.CharField(max_length=64, editable=False)
    source_digest = models.CharField(max_length=64, editable=False)
    before_digest = models.CharField(max_length=64, editable=False)
    after_digest = models.CharField(max_length=64, editable=False)
    before_snapshot = models.JSONField(editable=False)
    after_snapshot = models.JSONField(editable=False)
    before_version = models.PositiveBigIntegerField(editable=False)
    after_version = models.PositiveBigIntegerField(editable=False)
    restored_from = models.ForeignKey('self', on_delete=models.PROTECT, null=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at', 'id']
        constraints = [
            models.UniqueConstraint(fields=['design','user','key'], name='tpl_transition_key_unique'),
            models.CheckConstraint(condition=models.Q(before_version__gte=1, after_version=models.F('before_version')+1), name='tpl_transition_versions'),
            models.CheckConstraint(condition=(models.Q(action='upgrade', restored_from__isnull=True, before_snapshot__schema_version=1, after_snapshot__schema_version=2) | models.Q(action='restore', restored_from__isnull=False, before_snapshot__schema_version=2, after_snapshot__schema_version=1)), name='tpl_transition_direction'),
            *[models.CheckConstraint(condition=models.Q(**{name+'__regex':r'^[0-9a-f]{64}$'}), name='tpl_transition_'+name) for name in ('request_digest','source_digest','before_digest','after_digest')],
        ]
