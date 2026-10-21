"""Public error contract stays closed when Windows inspection fails."""
import subprocess
from unittest.mock import patch
from django.test import SimpleTestCase
from modules.media.storage import verify_windows_acl
from modules.portfolios.services import PortfolioProblem


class MediaWindowsAclErrorTests(SimpleTestCase):
    def setUp(self):
        verify_windows_acl.cache_clear()
        self.addCleanup(verify_windows_acl.cache_clear)

    def test_all_inspection_failures_keep_generic_503_without_acl_details(self):
        for failure in (OSError('synthetic private path'), ValueError('invalid encoding'),
                        subprocess.TimeoutExpired('powershell.exe', 10)):
            with self.subTest(failure=type(failure).__name__):
                with patch('modules.media.storage.inspect_private_acl', side_effect=failure):
                    with self.assertRaises(PortfolioProblem) as caught:
                        verify_windows_acl('synthetic-root')
                error = caught.exception
                self.assertEqual((error.code, error.status), ('media_unavailable', 503))
                self.assertEqual(error.message, 'Les permissions Windows du stockage doivent être privées.')
                self.assertIsNone(error.fields)

    def test_success_uses_inspection_and_retains_existing_cache_contract(self):
        with patch('modules.media.storage.inspect_private_acl') as inspect:
            verify_windows_acl('synthetic-root')
            verify_windows_acl('synthetic-root')
            inspect.assert_called_once_with('synthetic-root')
