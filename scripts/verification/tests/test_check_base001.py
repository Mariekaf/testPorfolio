"""Synthetic integrity regressions. No legacy runtime data or credentials."""
import hashlib
import importlib.util
from pathlib import Path
import tempfile
import unittest

SPEC = importlib.util.spec_from_file_location('base001_verifier', Path(__file__).resolve().parents[1]/'check_base001.py')
verifier = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(verifier)


class IntegrityTests(unittest.TestCase):
    def verify(self, name, expected, actual):
        with tempfile.TemporaryDirectory(prefix='integrity-test-') as folder:
            root = Path(folder)
            (root/name).write_bytes(actual)
            return verifier.verify_manifest(root, {'files': {name: hashlib.sha256(expected).hexdigest()}})

    def test_exact_lf_bytes_are_accepted(self):
        self.assertEqual(self.verify('sample.py', b'first\nsecond\n', b'first\nsecond\n'), 1)

    def test_windows_crlf_gitignore_is_accepted(self):
        self.assertEqual(self.verify('.gitignore', b'generated/\ncache/\n', b'generated/\r\ncache/\r\n'), 1)

    def test_utf8_crlf_json_is_accepted(self):
        raw = '{\n  "title": "Échantillon 東京"\n}\n'.encode('utf-8')
        self.assertEqual(self.verify('sample.json', raw, raw.replace(b'\n', b'\r\n')), 1)

    def test_mixed_line_endings_only_are_accepted(self):
        self.assertEqual(self.verify('sample.md', b'a\nb\n', b'a\r\nb\n'), 1)

    def test_real_text_change_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'Checksum mismatch'):
            self.verify('sample.py', b'original\n', b'changed\r\n')

    def test_added_whitespace_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'Checksum mismatch'):
            self.verify('sample.js', b'original\n', b'original \r\n')

    def test_lone_carriage_return_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'Checksum mismatch'):
            self.verify('sample.css', b'original\n', b'original\r')

    def test_bom_is_not_silently_removed(self):
        with self.assertRaisesRegex(ValueError, 'Checksum mismatch'):
            self.verify('sample.json', b'{}\n', b'\xef\xbb\xbf{}\r\n')

    def test_invalid_utf8_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'Checksum mismatch'):
            self.verify('sample.md', b'original\n', b'\xfforiginal\r\n')

    def test_binary_file_is_never_normalized(self):
        raw = b'\x89PNG\r\n\x1a\nsynthetic\n'
        self.assertEqual(self.verify('sample.png', raw, raw), 1)
        with self.assertRaisesRegex(ValueError, 'Checksum mismatch'):
            self.verify('sample.png', raw, raw.replace(b'\r\n', b'\n'))

    def test_unknown_extension_remains_byte_exact(self):
        with self.assertRaisesRegex(ValueError, 'Checksum mismatch'):
            self.verify('sample.bin', b'original\n', b'original\r\n')

    def test_manifest_path_cannot_escape_root(self):
        with tempfile.TemporaryDirectory(prefix='integrity-test-') as folder:
            root = Path(folder)/'inside'
            root.mkdir()
            with self.assertRaisesRegex(ValueError, 'escapes its root'):
                verifier.verify_manifest(root, {'files': {'../outside': 'unused'}})


if __name__ == '__main__':
    unittest.main()
