from django.db import migrations

def provision(apps,schema_editor):
    alias=schema_editor.connection.alias
    User=apps.get_model('identity','User');Account=apps.get_model('accounts','Account');Membership=apps.get_model('accounts','AccountMembership')
    for user in User.objects.using(alias).order_by('pk').iterator():
        account=Account.objects.using(alias).filter(owner_id=user.pk,kind='personal').first()
        if account is None:
            account=Account.objects.using(alias).create(owner_id=user.pk,kind='personal',name='Mon espace')
            Membership.objects.using(alias).create(account_id=account.pk,user_id=user.pk,role='admin',is_active=True)
        else:
            members=list(Membership.objects.using(alias).filter(account_id=account.pk))
            if not account.is_active or len(members)!=1 or members[0].user_id!=user.pk or members[0].role!='admin' or not members[0].is_active:
                raise RuntimeError('Personal account provisioning blocked: inconsistent ownership/membership; no values logged.')

class Migration(migrations.Migration):
    dependencies=[('accounts','0001_initial')]
    operations=[migrations.RunPython(provision,migrations.RunPython.noop)]
