"""Verify BASE-001 reference and synthetic fixtures; never reads runtime data."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / 'tests' / 'fixtures' / 'base001'


def read_json(path):
    return json.loads(path.read_text(encoding='utf-8'))


def verify_manifest(base, manifest):
    for name, expected in manifest['files'].items():
        path = (base / name).resolve()
        if not path.is_relative_to(base.resolve()):
            raise ValueError('Manifest path escapes its root')
        if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise ValueError('Checksum mismatch: ' + name)
    return len(manifest['files'])


def check(condition, message):
    if not condition:
        raise ValueError(message)


def main():
    count = verify_manifest(ROOT, read_json(ROOT / 'docs/compatibility/legacy-source-manifest.json'))
    print(f'Historical reference: {count} files unchanged (SHA-256).')
    count = verify_manifest(FIXTURE, read_json(FIXTURE / 'manifest.json'))
    print(f'Synthetic fixture: {count} checksums verified.')
    spec = importlib.util.spec_from_file_location('base001_legacy', ROOT / 'server.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # Does not call initialize or launch a server.
    value = read_json(FIXTURE / 'legacy-content.json')
    check(module.validate(copy.deepcopy(value)) == {k: v for k, v in value.items() if k != 'revision'}, 'Fixture validation changed data')
    check([p['slug'] for p in value['projects']] == ['alpha', 'beta', 'gamma'], 'Project order changed')
    check([p['slug'] for p in value['projects'] if p['published']] == ['alpha', 'gamma'], 'Publication flags changed')
    check('東京' in value['site']['aboutText'] and '\n\n' in value['site']['aboutText'], 'Unicode/paragraph sample missing')
    references = {value['site']['photo']}
    references.update(p['cover'] for p in value['projects'] if p['cover'])
    references.update(s['image'] for p in value['projects'] for s in p['sections'] if s['image'])
    for reference in references:
        check((FIXTURE / reference.lstrip('/')).is_file(), 'Referenced media missing')
    check('/uploads/33333333333333333333333333333333.png' not in references, 'Orphan fixture unexpectedly referenced')
    print('Fixture accepted without truncation; order, drafts, Unicode and media references verified.')
    print('No runtime content, credentials, initialization or CORE-001 dependency used.')


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        print('BASE-001 verification failed: ' + str(error), file=sys.stderr)
        sys.exit(1)
