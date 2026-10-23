"""Private initialization must never adopt or alter an existing user directory."""
import os
from pathlib import Path
import tempfile
import unittest
from scripts.development.initialize_private_media import initialize

class PrivateMediaInitializationTests(unittest.TestCase):
    def test_new_dedicated_directory_has_marker_and_private_mode(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'fresh-media';initialize(path)
            self.assertEqual((path/'.portfolio-media-v1').read_bytes(),b'portfolio-media-v1\n')
            if os.name!='nt':self.assertEqual(path.stat().st_mode & 0o077,0)

    def test_existing_user_directory_is_never_adopted_or_changed(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder);sentinel=path/'synthetic-user-file.txt';sentinel.write_bytes(b'preserve exactly')
            before=path.stat().st_mode
            with self.assertRaises(ValueError):initialize(path)
            self.assertEqual(sentinel.read_bytes(),b'preserve exactly')
            self.assertEqual(path.stat().st_mode,before)
            self.assertFalse((path/'.portfolio-media-v1').exists())

    def test_legacy_local_directory_is_not_created_or_used(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'.local'/'media'
            with self.assertRaises(ValueError):initialize(path)
            self.assertFalse((Path(folder)/'.local').exists())
