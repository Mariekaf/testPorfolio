"""Offline policy tests plus real Windows-only DACL tests on fresh empty directories."""
import base64
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from scripts.development.initialize_private_media import initialize

SOURCE = Path(__file__).resolve().parents[3] / 'backend/modules/media/windows_acl.py'
spec = importlib.util.spec_from_file_location('media_windows_acl_checks', SOURCE)
acl = importlib.util.module_from_spec(spec)
spec.loader.exec_module(acl)
USER = 'S-1-5-21-100-200-300-1001'
OTHER = 'S-1-5-21-100-200-300-1002'


def report(**changes):
    return dict(current_sid=USER, owner_sid=USER, dacl_present=True,
                allow_sids=['S-1-5-18', 'S-1-5-32-544', 'S-1-3-4']) | changes


class WindowsDaclPolicyTests(unittest.TestCase):
    def test_python313_owner_rights_acl_is_private(self):
        self.assertTrue(acl.acl_is_private(report()))

    def test_explicit_user_and_trusted_system_owners(self):
        for owner in (USER, 'S-1-5-18', 'S-1-5-32-544'):
            with self.subTest(owner=owner):
                self.assertTrue(acl.acl_is_private(report(owner_sid=owner, allow_sids=[USER, 'S-1-3-4'])))

    def test_owner_rights_never_authorizes_an_untrusted_owner(self):
        for entries in ([USER], ['S-1-3-4'], ['S-1-5-18', 'S-1-3-4']):
            self.assertFalse(acl.acl_is_private(report(owner_sid=OTHER, allow_sids=entries)))

    def test_public_unknown_and_creator_owner_principals_rejected(self):
        for sid in ('S-1-1-0', 'S-1-5-11', 'S-1-5-32-545', 'S-1-3-0', OTHER, 'unknown'):
            with self.subTest(sid=sid):
                self.assertFalse(acl.acl_is_private(report(allow_sids=[USER, sid])))

    def test_null_empty_and_malformed_dacl_reports_rejected(self):
        cases = [None, {}, [], report(dacl_present=False), report(dacl_present=1),
                 report(allow_sids=[]), report(allow_sids=None), report(allow_sids=USER),
                 report(allow_sids=[None]), report(owner_sid=None), report(current_sid='invalid'),
                 report(current_sid=None), report(extra=True)]
        for value in cases:
            with self.subTest(value=value):
                self.assertFalse(acl.acl_is_private(value))

    def test_transport_uses_encoded_command_and_path_in_environment_only(self):
        result = subprocess.CompletedProcess([], 0, json.dumps(report()), '')
        with patch.object(acl.subprocess, 'run', return_value=result) as run:
            acl.inspect_private_acl('C:/synthetic/é & quoted storage')
        args, kwargs = run.call_args
        command = args[0]
        self.assertEqual(command[:4], ['powershell.exe', '-NoProfile', '-NonInteractive', '-EncodedCommand'])
        self.assertEqual(base64.b64decode(command[4]).decode('utf-16-le'), acl.INSPECT_DACL)
        self.assertEqual(kwargs['env']['MEDIA001_ACL_PATH'], 'C:/synthetic/é & quoted storage')
        self.assertEqual(kwargs['encoding'], 'utf-8')
        self.assertEqual(kwargs['timeout'], 10)

    def test_inspection_errors_and_unsafe_reports_fail_closed(self):
        for status, output in ((1, ''), (0, 'not json'), (0, '{}'), (0, json.dumps(report(owner_sid=OTHER)))):
            with self.subTest(status=status, output=output):
                with patch.object(acl.subprocess, 'run', return_value=subprocess.CompletedProcess([], status, output, '')):
                    with self.assertRaises(OSError):
                        acl.inspect_private_acl('synthetic')
        with patch.object(acl.subprocess, 'run', side_effect=subprocess.TimeoutExpired('powershell.exe', 10)):
            with self.assertRaises(subprocess.TimeoutExpired):
                acl.inspect_private_acl('synthetic')


@unittest.skipUnless(os.name == 'nt' and sys.version_info[:2] == (3, 13),
                     'Requires native Windows and Python 3.13; not a Linux validation')
class WindowsDaclIntegrationTests(unittest.TestCase):
    def test_python313_temp_directory_and_marker_do_not_require_admin(self):
        with tempfile.TemporaryDirectory(prefix='media_acl_é_') as folder:
            acl.inspect_private_acl(folder)
            child = Path(folder) / 'inherited'
            child.mkdir()  # Inherited OI/CI entries, unlike explicit mkdir(0700).
            acl.inspect_private_acl(child)

    def test_initializer_and_temporary_test_storage_remain_private(self):
        with tempfile.TemporaryDirectory(prefix='media_acl_') as folder:
            root = Path(folder) / 'fresh'
            initialize(root)
            acl.inspect_private_acl(root)
            with tempfile.TemporaryDirectory(dir=root) as test_storage:
                acl.inspect_private_acl(test_storage)

    def test_public_allow_is_rejected_even_with_owner_rights_and_deny(self):
        # No user data: intentionally unsafe ACL exists only on this empty test dir.
        with tempfile.TemporaryDirectory(prefix='media_acl_negative_') as folder:
            try:
                subprocess.run(['icacls', folder, '/grant', '*S-1-1-0:(OI)(CI)R'],
                               check=True, capture_output=True)
                with self.assertRaises(OSError):
                    acl.inspect_private_acl(folder)
                inherited = Path(folder) / 'inherited-public'
                inherited.mkdir()
                with self.assertRaises(OSError):
                    acl.inspect_private_acl(inherited)
                inherited.rmdir()
                subprocess.run(['icacls', folder, '/deny', '*S-1-1-0:(OI)(CI)W'],
                               check=True, capture_output=True)
                with self.assertRaises(OSError):
                    acl.inspect_private_acl(folder)
            finally:
                subprocess.run(['icacls', folder, '/remove', '*S-1-1-0'],
                               check=True, capture_output=True)
            acl.inspect_private_acl(folder)
