import json
import secrets
import tempfile
import uuid
from pathlib import Path
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.exceptions import ImproperlyConfigured
from django.db import DatabaseError, connection
from django.test import SimpleTestCase, TestCase
from jsonschema import Draft202012Validator

from config.environment import ROOT, load_configuration


class HealthTests(TestCase):
    def test_live_without_database_access(self):
        with patch('config.health.connection.cursor', side_effect=AssertionError('Liveness must not access DB')):
            response = self.client.get('/health/live')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['status'], 'ok')
        self.assertIn('no-store', response.headers['Cache-Control'])

    def test_ready_uses_real_postgresql_and_migrated_table(self):
        self.assertEqual(connection.vendor, 'postgresql')
        response = self.client.get('/api/v1/health/ready')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'status': 'ok', 'service': 'portfolio-api', 'schema_version': 1})

    def test_unavailable_is_generic_without_secret_or_trace(self):
        with patch('config.health.connection.cursor', side_effect=DatabaseError('SENSITIVE_DATABASE_DETAIL')):
            response = self.client.get('/health/ready')
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()['status'], 'unavailable')
        self.assertNotIn('SENSITIVE_DATABASE_DETAIL', response.content.decode())
        self.assertIn('no-store', response.headers['Cache-Control'])

    def test_missing_initial_schema_is_not_ready(self):
        with patch('config.health.connection.cursor') as cursor:
            cursor.return_value.__enter__.return_value.execute.side_effect = [None, DatabaseError('missing table')]
            response = self.client.get('/health/ready')
        self.assertEqual(response.status_code, 503)

    def test_health_aliases_and_no_business_routes(self):
        for path in ['/health/live', '/health/ready', '/api/v1/health/live', '/api/v1/health/ready']:
            self.assertEqual(self.client.get(path).status_code, 200)
        for path in ['/api/v1/accounts', '/api/v1/account-memberships', '/admin/']:
            self.assertEqual(self.client.get(path).status_code, 404)

    def test_health_contract_matches_responses_and_examples(self):
        schema = json.loads((ROOT/'contracts/schemas/health/response.v1.json').read_text(encoding='utf-8'))
        validator = Draft202012Validator(schema)
        validator.validate(self.client.get('/health/ready').json())
        for name in ['health-ok.json', 'health-unavailable.json']:
            validator.validate(json.loads((ROOT/'contracts/examples'/name).read_text(encoding='utf-8')))
        self.assertTrue(list(validator.iter_errors({'status': 'ok'})))
        self.assertTrue(list(validator.iter_errors({'status': 'ok', 'service': 'portfolio-api', 'schema_version': 2})))

    def test_user_has_uuid_primary_key_without_seeded_personal_data(self):
        user = get_user_model().objects.create_user(email='fixture@example.test', first_name='Synthetic', last_name='Fixture', password=secrets.token_urlsafe(24))
        self.assertIsInstance(user.pk, uuid.UUID)
        self.assertNotEqual(user.password, '')
        self.assertFalse(user.is_superuser)


class ConfigurationTests(SimpleTestCase):
    def test_missing_config_fails_without_initializing_anything(self):
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder)/'missing.json'
            with patch.dict('os.environ', {'SAAS_CONFIG_FILE': str(target)}):
                with self.assertRaises(ImproperlyConfigured):
                    load_configuration()
            self.assertFalse(target.exists())

    def test_invalid_config_does_not_echo_values(self):
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder)/'bad.json'
            target.write_text('{"private":"DO_NOT_LOG"}', encoding='utf-8')
            with patch.dict('os.environ', {'SAAS_CONFIG_FILE': str(target)}):
                with self.assertRaises(ImproperlyConfigured) as error:
                    load_configuration()
            self.assertNotIn('DO_NOT_LOG', str(error.exception))


class LocalInitializationTests(SimpleTestCase):
    def load_initializer(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location('local_initializer', ROOT/'scripts/development/initialize_development.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_native_initialization_is_idempotent_and_docker_free(self):
        import contextlib
        import io
        module = self.load_initializer()
        with tempfile.TemporaryDirectory() as folder, patch.object(module, 'ROOT', Path(folder)), patch.object(module.subprocess, 'run') as git:
            git.return_value.returncode = 1
            with contextlib.redirect_stdout(io.StringIO()):
                module.initialize('native', 5433)
                path = Path(folder)/'infra/env/development.local.json'
                original = path.read_bytes()
                module.initialize('native', 5433)
            self.assertEqual(path.read_bytes(), original)
            self.assertFalse((path.parent/'development.local.env').exists())
            self.assertNotIn('bootstrap_password', json.loads(original))
            self.assertTrue(all(call.args[0][0] == 'git' for call in git.call_args_list))

    def test_existing_mode_or_port_cannot_be_overwritten(self):
        import contextlib
        import io
        module = self.load_initializer()
        with tempfile.TemporaryDirectory() as folder, patch.object(module, 'ROOT', Path(folder)), patch.object(module.subprocess, 'run') as git:
            git.return_value.returncode = 1
            with contextlib.redirect_stdout(io.StringIO()):
                module.initialize('native', 5433)
            path = Path(folder)/'infra/env/development.local.json'
            original = path.read_bytes()
            for mode, port in [('docker',5433),('native',5434)]:
                with self.assertRaises(ValueError):
                    module.initialize(mode, port)
            self.assertEqual(path.read_bytes(), original)

    def test_docker_settings_generated_without_printing_credentials(self):
        import contextlib
        import io
        module = self.load_initializer()
        output = io.StringIO()
        with tempfile.TemporaryDirectory() as folder, patch.object(module, 'ROOT', Path(folder)), patch.object(module.subprocess, 'run') as git:
            git.return_value.returncode = 1
            with contextlib.redirect_stdout(output):
                module.initialize('docker', 5433)
            config = json.loads((Path(folder)/'infra/env/development.local.json').read_text())
            self.assertNotIn(config['secret_key'], output.getvalue())
            self.assertNotIn(config['bootstrap_password'], output.getvalue())
            self.assertTrue((Path(folder)/'infra/env/development.local.env').is_file())


class MaintenancePreflightTests(SimpleTestCase):
    def test_unavailable_maintenance_fails_without_fallback(self):
        from config.database_checks import check_test_maintenance_access
        import psycopg
        from django.conf import settings
        with patch('config.database_checks.psycopg.connect', side_effect=psycopg.OperationalError('PRIVATE_DETAIL')):
            with self.assertRaises(ValueError) as error:
                check_test_maintenance_access(settings.CONFIG['database'])
        self.assertIn('no test database action performed', str(error.exception))
        self.assertNotIn('PRIVATE_DETAIL', str(error.exception))

    def test_test_runner_does_not_create_databases_if_preflight_fails(self):
        from config.test_runner import PostgreSQLTestRunner
        with patch('config.test_runner.check_test_maintenance_access', side_effect=ValueError('maintenance denied')), patch('django.test.runner.DiscoverRunner.setup_databases') as setup:
            with self.assertRaisesRegex(ValueError, 'maintenance denied'):
                PostgreSQLTestRunner().setup_databases()
            setup.assert_not_called()
