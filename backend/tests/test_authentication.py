"""Synthetic data only, isolated PostgreSQL test database."""
import secrets
from urllib.parse import parse_qs, urlsplit
from datetime import timedelta
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.sessions.models import Session
from django.core import mail
from django.db import IntegrityError, transaction
from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIClient

@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class AuthenticationTests(TestCase):
    def setUp(self):
        self.password=secrets.token_urlsafe(24)
        self.data=dict(email='synthetic@example.test',first_name='Synthetic',last_name='Tester',password=self.password,password_confirmation=self.password)
        self.client=APIClient(enforce_csrf_checks=True)

    def post(self,route,data,client=None):
        client=client or self.client
        token=client.get('/api/v1/auth/csrf').json()['csrf_token']
        return client.post('/api/v1/auth/'+route,data,format='json',HTTP_X_CSRFTOKEN=token)

    def register(self):
        self.assertEqual(self.post('register',self.data).status_code,201)

    def login(self,client=None,password=None):
        return self.post('login',dict(email=self.data['email'],password=password or self.password),client)

    def test_registration_hashes_without_login(self):
        self.register(); user=get_user_model().objects.get()
        self.assertTrue(user.check_password(self.password))
        self.assertNotEqual(user.password,self.password)
        self.assertFalse(user.is_staff)
        self.assertEqual(self.client.get('/api/v1/auth/me').status_code,401)

    def test_anonymous_csrf(self):
        for route in ['register','login','logout','password-reset','password-reset/confirm']:
            self.assertEqual(self.client.post('/api/v1/auth/'+route,{},format='json').status_code,403)

    def test_validation_and_mass_assignment(self):
        for changes in [dict(first_name=''),dict(last_name='x'*101),dict(email='bad'),dict(password='short',password_confirmation='short'),dict(password_confirmation='different'),dict(is_staff=True)]:
            self.assertEqual(self.post('register',self.data|changes).status_code,400)
        self.assertFalse(get_user_model().objects.exists())

    def test_case_insensitive_database_uniqueness(self):
        self.assertEqual(self.post('register',self.data|dict(email=' SYNTHETIC@EXAMPLE.TEST ')).status_code,201)
        self.assertEqual(get_user_model().objects.get().email,self.data['email'])
        self.assertEqual(self.post('register',self.data).status_code,400)
        with self.assertRaises(IntegrityError),transaction.atomic():
            get_user_model().objects.bulk_create([get_user_model()(email='SYNTHETIC@example.test')])

    def test_generic_login_and_inactive_user(self):
        unknown=self.login().json(); self.register()
        self.assertEqual(self.login(password='incorrect').json(),unknown)
        get_user_model().objects.update(is_active=False)
        self.assertEqual(self.login().json(),unknown)

    def test_session_logout_rotation_and_expiry(self):
        self.register(); self.assertEqual(self.login().status_code,200)
        key=self.client.cookies[settings.SESSION_COOKIE_NAME].value
        self.assertTrue(self.client.cookies[settings.SESSION_COOKIE_NAME]['httponly'])
        self.assertEqual(self.client.cookies[settings.SESSION_COOKIE_NAME]['samesite'],'Strict')
        me=self.client.get('/api/v1/auth/me')
        self.assertEqual(me.json()['user']['email'],self.data['email'])
        self.assertIn('no-store',me.headers['Cache-Control'])
        self.post('logout',{})
        self.assertFalse(Session.objects.filter(pk=key).exists())
        self.assertEqual(self.client.get('/api/v1/auth/me').status_code,401)
        self.login(); self.assertNotEqual(key,self.client.cookies[settings.SESSION_COOKIE_NAME].value)
        Session.objects.update(expire_date=timezone.now()-timedelta(seconds=1))
        self.assertEqual(self.client.get('/api/v1/auth/me').status_code,401)

    def reset_payload(self):
        self.post('password-reset',dict(email=self.data['email']))
        url=next(line for line in mail.outbox[-1].body.splitlines() if line.startswith('http'))
        self.assertFalse(urlsplit(url).query)
        payload={k:v[0] for k,v in parse_qs(urlsplit(url).fragment).items()}
        new=secrets.token_urlsafe(24)
        return payload|dict(password=new,password_confirmation=new)

    def test_reset_single_use_and_all_sessions_revoked(self):
        unknown=self.post('password-reset',dict(email='absent@example.test')).json()
        self.register(); self.login()
        other=APIClient(enforce_csrf_checks=True); self.assertEqual(self.login(other).status_code,200)
        payload=self.reset_payload()
        self.assertEqual(self.post('password-reset',dict(email=self.data['email'])).json(),unknown)
        self.assertEqual(self.post('password-reset/confirm',payload).status_code,200)
        self.assertEqual(self.client.get('/api/v1/auth/me').status_code,401)
        self.assertEqual(other.get('/api/v1/auth/me').status_code,401)
        self.assertEqual(self.post('password-reset/confirm',payload).status_code,400)
        self.assertEqual(self.login(password=payload['password']).status_code,200)

    def test_invalid_expired_reset(self):
        self.register()
        for payload in [[],dict(uid='bad',token='bad')]:
            self.assertEqual(self.post('password-reset/confirm',payload).status_code,400)
        payload=self.reset_payload()
        with override_settings(PASSWORD_RESET_TIMEOUT=-1):
            self.assertEqual(self.post('password-reset/confirm',payload).status_code,400)

    @override_settings(AUTH_RATE_LIMITS={'login_ip':(20,300),'login_email':(1,300)})
    def test_shared_throttle(self):
        self.assertEqual(self.login().status_code,401)
        response=self.login(APIClient(enforce_csrf_checks=True))
        self.assertEqual(response.status_code,429)
        self.assertIn('Retry-After',response.headers)

    @override_settings(SESSION_COOKIE_SECURE=True,CSRF_COOKIE_SECURE=True)
    def test_secure_cookies(self):
        self.register(); response=self.login()
        for name in [settings.SESSION_COOKIE_NAME,settings.CSRF_COOKIE_NAME]:
            self.assertTrue(response.cookies[name]['secure'])

    def test_cross_origin_mutations_rejected(self):
        token=self.client.get('/api/v1/auth/csrf').json()['csrf_token']
        response=self.client.post('/api/v1/auth/register',self.data,format='json',HTTP_X_CSRFTOKEN=token,HTTP_ORIGIN='https://untrusted.example')
        self.assertEqual(response.status_code,403)

    def test_session_payload_never_exposes_password_or_permissions(self):
        self.register(); response=self.login()
        self.assertEqual(set(response.json()),{'user','expires_at'})
        self.assertEqual(set(response.json()['user']),{'id','email','first_name','last_name'})
        self.assertNotIn(self.password,response.content.decode())

    def test_me_is_bound_to_session_not_supplied_identity(self):
        self.register(); self.login()
        other=get_user_model().objects.create_user(email='another@example.test',password=secrets.token_urlsafe(24),first_name='Other',last_name='Synthetic')
        response=self.client.get('/api/v1/auth/me',{'user_id':str(other.pk)})
        self.assertEqual(response.json()['user']['email'],self.data['email'])

    def test_login_rotates_existing_anonymous_session(self):
        self.register()
        session=self.client.session;session['synthetic']='value';session.save()
        old=session.session_key
        self.login()
        self.assertNotEqual(old,self.client.cookies[settings.SESSION_COOKIE_NAME].value)
        self.assertFalse(Session.objects.filter(pk=old).exists())

    def test_email_delivery_failure_stays_generic_without_link_logging(self):
        from unittest.mock import patch
        self.register()
        with patch('modules.identity.views.send_mail',side_effect=RuntimeError('PRIVATE_SMTP_DETAIL')):
            with self.assertLogs('identity.mail',level='WARNING') as logs:
                response=self.post('password-reset',dict(email=self.data['email']))
        self.assertEqual(response.status_code,200)
        self.assertNotIn('PRIVATE_SMTP_DETAIL',str(logs.output))
        self.assertNotIn(self.data['email'],str(logs.output))

    def test_private_mailbox_permissions(self):
        import tempfile,os
        from pathlib import Path
        from django.core.mail import send_mail
        with tempfile.TemporaryDirectory() as folder:
            target=Path(folder)/'mailbox'
            with override_settings(EMAIL_BACKEND='modules.identity.mailbox.PrivateMailboxBackend',EMAIL_FILE_PATH=target):
                self.assertEqual(send_mail('Synthetic','Synthetic body','no-reply@example.test',['synthetic@example.test']),1)
            files=list(target.glob('*.log'));self.assertEqual(len(files),1)
            if os.name!='nt':
                self.assertEqual(target.stat().st_mode&0o777,0o700)
                self.assertEqual(files[0].stat().st_mode&0o777,0o600)

    def test_migration_guard_refuses_ambiguous_identities_without_edits(self):
        import importlib
        from types import SimpleNamespace
        from unittest.mock import Mock
        migration=importlib.import_module('modules.identity.migrations.0002_authenticationlimit_authsession_alter_user_options_and_more')
        users=[SimpleNamespace(email='synthetic@example.test',first_name='Synthetic',last_name='Tester',save=Mock()),
               SimpleNamespace(email='SYNTHETIC@example.test',first_name='Other',last_name='Tester',save=Mock())]
        model=Mock();model.objects.using.return_value.all.return_value=users
        apps=Mock();apps.get_model.return_value=model
        editor=SimpleNamespace(connection=SimpleNamespace(alias='default'))
        with self.assertRaisesRegex(RuntimeError,'manual review') as error:
            migration.prepare_existing_users(apps,editor)
        self.assertNotIn('synthetic@example.test',str(error.exception))
        for user in users:user.save.assert_not_called()

    def test_cleanup_keeps_active_limits(self):
        import io
        from django.core.management import call_command
        from modules.identity.models import AuthenticationLimit
        AuthenticationLimit.objects.create(key='a'*64,attempts=1,window_start=timezone.now()-timedelta(days=2))
        AuthenticationLimit.objects.create(key='b'*64,attempts=1,window_start=timezone.now())
        call_command('cleanup_auth_limits',stdout=io.StringIO())
        self.assertEqual(list(AuthenticationLimit.objects.values_list('key',flat=True)),['b'*64])

    def test_session_matches_versioned_contract(self):
        import json
        from config.environment import ROOT
        from jsonschema import Draft202012Validator, FormatChecker
        self.register()
        schema=json.loads((ROOT/'contracts/schemas/auth/session.v1.json').read_text(encoding='utf-8'))
        Draft202012Validator(schema,format_checker=FormatChecker()).validate(self.login().json())
