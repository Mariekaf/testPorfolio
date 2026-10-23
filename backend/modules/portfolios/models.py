import uuid
from django.db import models
from django.db.models.functions import Lower
from modules.accounts.models import Account

class Portfolio(models.Model):
    class Type(models.TextChoices):
        PERSONAL='personal','Personnel'
        PROFESSIONAL='professional','Professionnel'
        BUSINESS='business','Entreprise'
    id=models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False)
    account=models.ForeignKey(Account,on_delete=models.PROTECT,related_name='portfolios')
    name=models.CharField(max_length=100)
    slug=models.SlugField(max_length=110)
    description=models.CharField(max_length=500,blank=True)
    portfolio_type=models.CharField(max_length=20,choices=Type.choices,default=Type.PERSONAL)
    status=models.CharField(max_length=16,default='draft',editable=False)
    visibility=models.CharField(max_length=16,default='private',editable=False)
    management_state=models.CharField(max_length=12,default='active')
    version=models.PositiveBigIntegerField(default=1)
    source_template_id=models.CharField(max_length=100,null=True,blank=True)
    source_template_version=models.CharField(max_length=30,null=True,blank=True)
    initial_theme_id=models.CharField(max_length=100,default='studio-neutral')
    initial_theme_version=models.CharField(max_length=30,default='1.0.0')
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now=True)
    deleted_at=models.DateTimeField(null=True,blank=True,db_index=True)

    class Meta:
        ordering=['-updated_at','-created_at','id']
        constraints=[
            models.CheckConstraint(condition=models.Q(status='draft'),name='port001_draft_only'),
            models.CheckConstraint(condition=models.Q(visibility='private'),name='port001_private_only'),
            models.UniqueConstraint('account',Lower('slug'),name='portfolio_account_slug_unique'),
            models.CheckConstraint(condition=models.Q(management_state__in=['active','archived']),name='portfolio_management_valid'),
            models.CheckConstraint(condition=models.Q(version__gte=1),name='portfolio_version_positive'),
            models.CheckConstraint(condition=models.Q(slug__regex=r'^[a-z0-9]+(?:-[a-z0-9]+)*$'),name='portfolio_slug_valid'),
            models.CheckConstraint(condition=models.Q(name__regex=r'^\S.{1,98}\S$'),name='portfolio_name_valid'),
            models.CheckConstraint(condition=(models.Q(source_template_id__isnull=True,source_template_version__isnull=True)|models.Q(source_template_id__isnull=False,source_template_version__isnull=False)),name='portfolio_template_pair'),
            models.CheckConstraint(condition=(models.Q(source_template_id__isnull=True)|models.Q(source_template_id__regex=r'^[a-z][a-z0-9-]*$',source_template_version__regex=r'^[0-9]+\.[0-9]+\.[0-9]+$')),name='portfolio_template_format'),
            models.CheckConstraint(condition=models.Q(initial_theme_id='studio-neutral',initial_theme_version='1.0.0'),name='portfolio_initial_theme_valid'),
        ]
