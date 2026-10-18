import uuid
from django.conf import settings
from django.db import models

class Account(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    kind = models.CharField(max_length=20, default='personal', choices=[('personal','Personnel'),('collaborative','Réservé')])
    owner = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.PROTECT,related_name='owned_accounts')
    name = models.CharField(max_length=100,default='Mon espace')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['owner'],condition=models.Q(kind='personal'),name='account_one_personal_per_user'),
            models.CheckConstraint(condition=models.Q(kind__in=['personal','collaborative']),name='account_kind_valid'),
        ]

class AccountMembership(models.Model):
    id = models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False)
    account = models.ForeignKey(Account,on_delete=models.CASCADE,related_name='memberships')
    user = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.PROTECT,related_name='account_memberships')
    role = models.CharField(max_length=12,default='admin',choices=[('admin','Administrateur'),('editor','Éditeur'),('viewer','Lecture')])
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['account','user'],name='membership_account_user_unique'),
            models.CheckConstraint(condition=models.Q(role__in=['admin','editor','viewer']),name='membership_role_valid'),
        ]
