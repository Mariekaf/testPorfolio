import uuid
from django.conf import settings
from django.db import migrations,models
import django.db.models.deletion

class Migration(migrations.Migration):
    initial=True
    dependencies=[('identity','0002_authenticationlimit_authsession_alter_user_options_and_more')]
    operations=[
        migrations.CreateModel(name='Account',fields=[
            ('id',models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False,serialize=False)),
            ('kind',models.CharField(max_length=20,default='personal',choices=[('personal','Personnel'),('collaborative','Réservé')])),
            ('name',models.CharField(max_length=100,default='Mon espace')),
            ('is_active',models.BooleanField(default=True)),
            ('created_at',models.DateTimeField(auto_now_add=True)),('updated_at',models.DateTimeField(auto_now=True)),
            ('owner',models.ForeignKey(to=settings.AUTH_USER_MODEL,on_delete=django.db.models.deletion.PROTECT,related_name='owned_accounts')),
        ]),
        migrations.CreateModel(name='AccountMembership',fields=[
            ('id',models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False,serialize=False)),
            ('role',models.CharField(max_length=12,default='admin',choices=[('admin','Administrateur'),('editor','Éditeur'),('viewer','Lecture')])),
            ('is_active',models.BooleanField(default=True)),
            ('created_at',models.DateTimeField(auto_now_add=True)),('updated_at',models.DateTimeField(auto_now=True)),
            ('account',models.ForeignKey(to='accounts.account',on_delete=django.db.models.deletion.CASCADE,related_name='memberships')),
            ('user',models.ForeignKey(to=settings.AUTH_USER_MODEL,on_delete=django.db.models.deletion.PROTECT,related_name='account_memberships')),
        ]),
        migrations.AddConstraint(model_name='account',constraint=models.UniqueConstraint(fields=['owner'],condition=models.Q(kind='personal'),name='account_one_personal_per_user')),
        migrations.AddConstraint(model_name='account',constraint=models.CheckConstraint(condition=models.Q(kind__in=['personal','collaborative']),name='account_kind_valid')),
        migrations.AddConstraint(model_name='accountmembership',constraint=models.UniqueConstraint(fields=['account','user'],name='membership_account_user_unique')),
        migrations.AddConstraint(model_name='accountmembership',constraint=models.CheckConstraint(condition=models.Q(role__in=['admin','editor','viewer']),name='membership_role_valid')),
    ]
