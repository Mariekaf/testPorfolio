"""Explicit personal provisioning. No repair of existing inconsistent memberships."""
from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Count
from .models import Account, AccountMembership

class AccountInconsistent(Exception):
    pass


def authorized_accounts(user):
    return Account.objects.filter(kind='personal',is_active=True,owner=user).annotate(
        member_count=Count('memberships',distinct=True)).filter(member_count=1,
        memberships__user=user,memberships__role='admin',memberships__is_active=True)


@transaction.atomic
def ensure_personal_account(user):
    locked=get_user_model().objects.select_for_update().get(pk=user.pk)
    if not locked.is_active:
        raise AccountInconsistent()
    account=Account.objects.select_for_update().filter(owner=locked,kind='personal').first()
    if account is None:
        account=Account.objects.create(owner=locked)
        AccountMembership.objects.create(account=account,user=locked,role='admin')
        return account
    memberships=list(account.memberships.all())
    if not account.is_active or len(memberships)!=1 or memberships[0].user_id!=locked.pk or memberships[0].role!='admin' or not memberships[0].is_active:
        raise AccountInconsistent()
    return account
