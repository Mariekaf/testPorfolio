import re
from django.db import migrations,models
from django.db.models.functions import Lower
import django.db.models.deletion

def backfill(apps,schema_editor):
    alias=schema_editor.connection.alias
    Portfolio=apps.get_model('portfolios','Portfolio');Account=apps.get_model('accounts','Account');Membership=apps.get_model('accounts','AccountMembership')
    # Validate all source rows before the first update; atomic migration also
    # rolls back updates when a later SQL constraint cannot be established.
    for item in Portfolio.objects.using(alias).order_by('pk').iterator():
        account=Account.objects.using(alias).filter(owner_id=item.owner_id,kind='personal').first()
        members=list(Membership.objects.using(alias).filter(account_id=account.pk)) if account else []
        if (not account or not account.is_active or len(members)!=1 or members[0].user_id!=item.owner_id or members[0].role!='admin' or not members[0].is_active
            or (item.account_id is not None and item.account_id!=account.pk)
            or not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*',item.slug)
            or not re.fullmatch(r'\S.{1,98}\S',item.name)
            or item.status!='draft' or item.visibility!='private'):
            raise RuntimeError('Portfolio migration blocked: incompatible source ownership, membership or metadata; no values logged.')
    for account in Account.objects.using(alias).filter(kind='personal').iterator():
        Portfolio.objects.using(alias).filter(owner_id=account.owner_id).update(account_id=account.pk)

class Migration(migrations.Migration):
    dependencies=[('portfolios','0002_expand_account_ownership')]
    operations=[
        migrations.RunPython(backfill,migrations.RunPython.noop),
        migrations.RunSQL("SET CONSTRAINTS ALL IMMEDIATE",reverse_sql=migrations.RunSQL.noop),
        migrations.AlterField(model_name='portfolio',name='account',field=models.ForeignKey(to='accounts.account',on_delete=django.db.models.deletion.PROTECT,related_name='portfolios')),
        migrations.AddConstraint(model_name='portfolio',constraint=models.UniqueConstraint('account',Lower('slug'),name='portfolio_account_slug_unique')),
        migrations.AlterField(model_name='portfolio',name='slug',field=models.SlugField(max_length=110)),
        migrations.AddConstraint(model_name='portfolio',constraint=models.CheckConstraint(condition=models.Q(management_state__in=['active','archived']),name='portfolio_management_valid')),
        migrations.AddConstraint(model_name='portfolio',constraint=models.CheckConstraint(condition=models.Q(version__gte=1),name='portfolio_version_positive')),
        migrations.AddConstraint(model_name='portfolio',constraint=models.CheckConstraint(condition=models.Q(slug__regex=r'^[a-z0-9]+(?:-[a-z0-9]+)*$'),name='portfolio_slug_valid')),
        migrations.AddConstraint(model_name='portfolio',constraint=models.CheckConstraint(condition=models.Q(name__regex=r'^\S.{1,98}\S$'),name='portfolio_name_valid')),
        migrations.AddConstraint(model_name='portfolio',constraint=models.CheckConstraint(condition=(models.Q(source_template_id__isnull=True,source_template_version__isnull=True)|models.Q(source_template_id__isnull=False,source_template_version__isnull=False)),name='portfolio_template_pair')),
        migrations.AddConstraint(model_name='portfolio',constraint=models.CheckConstraint(condition=(models.Q(source_template_id__isnull=True)|models.Q(source_template_id__regex=r'^[a-z][a-z0-9-]*$',source_template_version__regex=r'^[0-9]+\.[0-9]+\.[0-9]+$')),name='portfolio_template_format')),
        migrations.AddConstraint(model_name='portfolio',constraint=models.CheckConstraint(condition=models.Q(initial_theme_id='studio-neutral',initial_theme_version='1.0.0'),name='portfolio_initial_theme_valid')),
        migrations.AlterModelOptions(name='portfolio',options={'ordering':['-updated_at','-created_at','id']}),
    ]
