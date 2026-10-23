import uuid
from django.db import models

class Asset(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    account = models.ForeignKey('accounts.Account', on_delete=models.PROTECT, related_name='assets')
    original_name = models.CharField(max_length=180, blank=True)
    content_type = models.CharField(max_length=30, default='image/webp', editable=False)
    width = models.PositiveIntegerField()
    height = models.PositiveIntegerField()
    thumbnail_width = models.PositiveIntegerField()
    thumbnail_height = models.PositiveIntegerField()
    size = models.PositiveIntegerField()
    thumbnail_size = models.PositiveIntegerField()
    digest = models.CharField(max_length=64, blank=True)
    thumbnail_digest = models.CharField(max_length=64, blank=True)
    storage_key = models.CharField(max_length=64, unique=True, null=True, editable=False)
    status = models.CharField(max_length=12, default='ready', editable=False)
    rights_confirmed = models.BooleanField(default=False)
    version = models.PositiveBigIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    deleted_at = models.DateTimeField(null=True, editable=False)
    purged_at = models.DateTimeField(null=True, editable=False)

    class Meta:
        ordering = ['-created_at','id']
        constraints = [
            models.CheckConstraint(condition=models.Q(status__in=['ready','deleted','purged']),name='media_status_known'),
            models.CheckConstraint(condition=models.Q(content_type='image/webp',version__gte=1),name='media_safe_type_version'),
            models.CheckConstraint(condition=models.Q(status='purged') | models.Q(width__gte=1,height__gte=1,thumbnail_width__gte=1,thumbnail_height__gte=1,size__gte=1,thumbnail_size__gte=1,rights_confirmed=True,storage_key__isnull=False,storage_key__regex=r'^[0-9a-f]{64}$',digest__regex=r'^[0-9a-f]{64}$',thumbnail_digest__regex=r'^[0-9a-f]{64}$'),name='media_valid_variants'),
            models.CheckConstraint(condition=models.Q(status='ready',deleted_at__isnull=True,purged_at__isnull=True) | models.Q(status='deleted',deleted_at__isnull=False,purged_at__isnull=True) | models.Q(status='purged',deleted_at__isnull=False,purged_at__isnull=False,storage_key__isnull=True,size=0,thumbnail_size=0),name='media_lifecycle'),
        ]
