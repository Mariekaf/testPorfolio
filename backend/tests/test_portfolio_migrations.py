"""Exercise both historical entry points in a disposable PostgreSQL test DB."""
import secrets
from datetime import timedelta
from django.contrib.auth.hashers import make_password
from django.contrib.auth import get_user_model
from django.conf import settings
from django.contrib.sessions.backends.db import SessionStore
from rest_framework.test import APIClient
from django.core.management import call_command
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.db.migrations.recorder import MigrationRecorder
from django.test import TransactionTestCase
from django.utils import timezone

IDENTITY=('identity','0002_authenticationlimit_authsession_alter_user_options_and_more')
LEGACY=('portfolios','0001_initial')
ACCOUNT_SCHEMA=('accounts','0001_initial')
ACCOUNT_DATA=('accounts','0002_provision_personal_accounts')
EXPAND=('portfolios','0002_expand_account_ownership')
FINAL=('portfolios','0004_contract_legacy_owner')

class PortfolioMigrationTests(TransactionTestCase):
    def migrate(self,targets):
        executor=MigrationExecutor(connection);executor.migrate(targets)
        return MigrationExecutor(connection).loader.project_state([target for target in targets if target[1] is not None] or [IDENTITY]).apps

    def setUp(self):
        self.assertEqual(connection.vendor,'postgresql')
        self.assertTrue(connection.settings_dict['NAME'].startswith('test_'))
        self.latest=MigrationExecutor(connection).loader.graph.leaf_nodes()
        self.migrate([('portfolios',None),('accounts',None)])
        self.apps=MigrationExecutor(connection).loader.project_state([IDENTITY]).apps
        self.hash=make_password(secrets.token_urlsafe(24))
        self.user=self.apps.get_model('identity','User').objects.create(email='migration@example.test',first_name='Migration',last_name='Synthetic',password=self.hash)

    def tearDown(self):
        # Only this guarded disposable test DB is flushed. Restore the schema
        # even after intentionally blocked migrations before the next test.
        try:
            call_command('flush',verbosity=0,interactive=False)
            self.migrate(self.latest)
        finally:super().tearDown()

    def test_from_auth_only_preserves_identity_and_existing_session(self):
        Session=self.apps.get_model('sessions','Session')
        marker=secrets.token_hex(16)
        expires=timezone.now()+timedelta(hours=1)
        payload=SessionStore().encode({'_auth_user_id':str(self.user.pk),'_auth_user_backend':'django.contrib.auth.backends.ModelBackend','_auth_user_hash':get_user_model().objects.get(pk=self.user.pk).get_session_auth_hash(),'_session_expiry':expires.isoformat()})
        session=Session.objects.create(session_key=marker,session_data=payload,expire_date=expires)
        self.apps.get_model('identity','AuthSession').objects.create(session_id=session.pk,user_id=self.user.pk)
        apps=self.migrate(self.latest)
        user=apps.get_model('identity','User').objects.get(pk=self.user.pk)
        account=apps.get_model('accounts','Account').objects.get(owner_id=user.pk,kind='personal')
        membership=apps.get_model('accounts','AccountMembership').objects.get(account_id=account.pk,user_id=user.pk)
        self.assertEqual(user.password,self.hash);self.assertEqual(membership.role,'admin');self.assertTrue(membership.is_active)
        self.assertTrue(apps.get_model('sessions','Session').objects.filter(pk=marker,session_data=payload).exists())
        self.assertTrue(apps.get_model('identity','AuthSession').objects.filter(session_id=marker,user_id=user.pk).exists())
        client=APIClient();client.cookies[settings.SESSION_COOKIE_NAME]=marker
        response=client.get('/api/v1/auth/me')
        self.assertEqual(response.status_code,200)
        self.assertEqual(response.json()['user']['id'],str(user.pk))
        self.assertEqual(set(response.json()),{'user','expires_at'})
        self.migrate(self.latest)
        self.assertEqual(apps.get_model('accounts','Account').objects.count(),1)

    def test_from_legacy_preserves_all_metadata_and_deleted_rows(self):
        apps=self.migrate([LEGACY,IDENTITY])
        Portfolio=apps.get_model('portfolios','Portfolio')
        other_user=apps.get_model('identity','User').objects.create(email='second-migration@example.test',first_name='Second',last_name='Synthetic',password=self.hash)
        other_item=Portfolio.objects.create(owner_id=other_user.pk,name='Second owner portfolio',slug='second-owner')
        old=timezone.now()-timedelta(days=9)
        first=Portfolio.objects.create(owner_id=self.user.pk,name='Existing portfolio',slug='existing',description='Synthetic description',portfolio_type='professional')
        removed=Portfolio.objects.create(owner_id=self.user.pk,name='Deleted portfolio',slug='deleted',deleted_at=old)
        Portfolio.objects.filter(pk=first.pk).update(created_at=old,updated_at=old)
        apps=self.migrate(self.latest)
        result=apps.get_model('portfolios','Portfolio').objects.get(pk=first.pk)
        self.assertEqual((result.name,result.slug,result.description,result.portfolio_type),('Existing portfolio','existing','Synthetic description','professional'))
        self.assertEqual((result.created_at,result.updated_at),(old,old))
        self.assertEqual((result.status,result.visibility,result.management_state,result.version),('draft','private','active',1))
        self.assertEqual(result.account.owner_id,self.user.pk)
        removed=apps.get_model('portfolios','Portfolio').objects.get(pk=removed.pk)
        self.assertEqual(removed.deleted_at,old);self.assertEqual(removed.account_id,result.account_id)
        self.assertEqual((result.initial_theme_id,result.initial_theme_version),('studio-neutral','1.0.0'))
        other_item=apps.get_model('portfolios','Portfolio').objects.get(pk=other_item.pk)
        self.assertEqual(other_item.account.owner_id,other_user.pk)
        self.assertNotEqual(other_item.account_id,result.account_id)

    def test_inconsistent_membership_blocks_without_repair(self):
        apps=self.migrate([ACCOUNT_SCHEMA,IDENTITY])
        account=apps.get_model('accounts','Account').objects.create(owner_id=self.user.pk)
        member=apps.get_model('accounts','AccountMembership').objects.create(account_id=account.pk,user_id=self.user.pk,role='viewer')
        with self.assertRaisesRegex(RuntimeError,'inconsistent'):
            self.migrate([ACCOUNT_DATA])
        member.refresh_from_db();self.assertEqual(member.role,'viewer')
        self.assertFalse(MigrationRecorder(connection).migration_qs.filter(app='accounts',name=ACCOUNT_DATA[1]).exists())

    def test_incompatible_slug_blocks_without_changes(self):
        apps=self.migrate([LEGACY,IDENTITY])
        item=apps.get_model('portfolios','Portfolio').objects.create(owner_id=self.user.pk,name='Existing portfolio',slug='Old_Slug')
        with self.assertRaisesRegex(RuntimeError,'incompatible'):
            self.migrate(self.latest)
        apps=MigrationExecutor(connection).loader.project_state([EXPAND]).apps
        item=apps.get_model('portfolios','Portfolio').objects.get(pk=item.pk)
        self.assertEqual(item.slug,'Old_Slug');self.assertIsNone(item.account_id)

    def test_wrong_preassigned_account_is_not_replaced(self):
        apps=self.migrate([EXPAND])
        user=apps.get_model('identity','User').objects.create(email='wrong@example.test',first_name='Other',last_name='Synthetic',password=self.hash)
        other=apps.get_model('accounts','Account').objects.create(owner_id=user.pk)
        apps.get_model('accounts','AccountMembership').objects.create(account_id=other.pk,user_id=user.pk)
        item=apps.get_model('portfolios','Portfolio').objects.create(owner_id=self.user.pk,account_id=other.pk,name='Wrong ownership',slug='wrong-owner')
        with self.assertRaisesRegex(RuntimeError,'incompatible'):
            self.migrate(self.latest)
        item.refresh_from_db();self.assertEqual(item.account_id,other.pk)
