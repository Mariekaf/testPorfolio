"""Fail-closed, bounded Git bundle loader; never reads user media or .local."""
import copy
import hashlib
import json
import re
from pathlib import Path
from urllib.parse import urlsplit

from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource

ROOT = Path(__file__).resolve().parents[3]
CATEGORIES = ('minimal', 'editorial', 'retro', 'cyberpunk', 'gaming', 'immersive')
VARIANTS = {
    'hero': ('hero-centered', 'hero-split'),
    'about': ('about-compact', 'about-column'),
    'projects': ('projects-grid', 'projects-featured'),
    'skills': ('skills-list', 'skills-sidebar'),
    'contact': ('contact-simple', 'contact-panel'),
}
LAYOUTS = {'minimal': 'minimal-stack', 'editorial': 'editorial-grid'}
LAYOUT_VARIANTS = {'minimal-stack': {v[0] for v in VARIANTS.values()}, 'editorial-grid': {v[1] for v in VARIANTS.values()}}
LIMIT = 256 * 1024

class RegistryInvalid(ValueError):
    """Public callers must return a generic 503, never filesystem details."""


def require(condition):
    if not condition:
        raise RegistryInvalid('Invalid template registry.')


def strict_json(raw):
    require(len(raw) <= LIMIT)
    def pairs(values):
        result = {}
        for key, value in values:
            require(key not in result)
            result[key] = value
        return result
    return json.loads(raw.decode("utf-8"), object_pairs_hook=pairs, parse_constant=lambda value: require(False))


def validate_snapshot(snapshot):
    """Cross-document invariants, after JSON Schema validation."""
    composition = snapshot['composition']
    sections = composition['sections']
    ids = [s['id'] for s in sections]
    require(len(ids) == len(set(ids)))
    policy = {s['id']: s for s in sections}
    for section in sections:
        require(section['variant'] in VARIANTS[section['type']])
        require(not section['required'] or section['visible'])
        for values in section['presentation_policy'].values():
            require(len(values) == len(set(values)))
    for document in ['content', 'presentation']:
        references = [s['section_id'] for s in snapshot[document]['sections']]
        require(len(references) == len(set(references)) and set(references) == set(ids))
    project_ids = set()
    for section in snapshot['content']['sections']:
        require(section['type'] == policy[section['section_id']]['type'])
        if section['type'] == 'projects':
            for project in section['data']['items']:
                require(project['id'] not in project_ids)
                project_ids.add(project['id'])
                if project['url'] is not None:
                    url = urlsplit(project['url'])
                    require(url.scheme == 'https' and bool(url.hostname) and not url.username and not url.password)
                    require(not any(ord(c) < 33 for c in project['url']))
    for section in snapshot['presentation']['sections']:
        allowed = policy[section['section_id']]['presentation_policy']
        require(all(value in allowed[key] for key, value in section['settings'].items()))
    overrides = snapshot['customization']['sections']
    require(len({s['section_id'] for s in overrides}) == len(overrides))
    for section in overrides:
        require(section['section_id'] in policy)
        source = policy[section['section_id']]
        if 'visible' in section:
            require(source['toggleable'] or section['visible'] == source['visible'])
            require(not source['required'] or section['visible'])
        require(all(value in source['presentation_policy'][key] for key, value in section.get('presentation', {}).items()))
    order = snapshot['customization'].get('section_order', ids)
    require(len(order) == len(ids) and set(order) == set(ids))
    require(all(s['reorderable'] or order.index(s['id']) == ids.index(s['id']) for s in sections))


class TemplateRegistry:
    def __init__(self, root=None):
        self.root = Path(root or ROOT).resolve()
        self.base = self.root / 'contracts/templates'
        self._entries = {}
        try:
            self._load()
        except RegistryInvalid:
            raise
        except Exception:
            # No filesystem paths or parsed contents escape to API/log messages.
            raise RegistryInvalid('Invalid template registry.') from None

    def _read(self, path):
        require(path.resolve().is_relative_to((self.root / 'contracts').resolve()))
        require(path.stat().st_size <= LIMIT)
        return path.read_bytes()

    def _schema(self, path):
        def retrieve(uri):
            from urllib.parse import urlparse
            require(urlparse(uri).scheme == 'file')
            # Windows file URI starts /C:/; Path.from_uri handles both platforms.
            target = Path.from_uri(uri).resolve()
            require(target.is_relative_to((self.root / 'contracts/schemas').resolve()))
            return Resource.from_contents(strict_json(self._read(target)))
        schema = strict_json(self._read(path))
        Draft202012Validator.check_schema(schema)
        return Draft202012Validator({'$ref': path.resolve().as_uri()}, registry=Registry(retrieve=retrieve), format_checker=FormatChecker())

    def _load(self):
        manifest = strict_json(self._read(self.base / 'manifest.v1.json'))
        require(set(manifest) == {'schema_version', 'revision', 'renderer_version', 'entries'})
        require(type(manifest['schema_version']) is int and manifest['schema_version'] == 1)
        require(type(manifest['revision']) is int and manifest['revision'] >= 1)
        require(manifest['renderer_version'] == '1.0.0')
        require(isinstance(manifest['entries'], list) and 0 < len(manifest['entries']) <= 32)
        descriptor_validator = self._schema(self.root / 'contracts/schemas/templates/template.v1.json')
        snapshot_validator = self._schema(self.root / 'contracts/schemas/templates/documents/snapshot.v1.json')
        theme = strict_json(self._read(self.root / 'contracts/themes/studio-neutral.v1.json'))
        self._schema(self.root / 'contracts/schemas/themes/theme.v1.json').validate(theme)
        require((theme['id'], theme['version']) == ('studio-neutral', '1.0.0'))
        for entry in manifest['entries']:
            require(set(entry) == {'id', 'version', 'availability', 'files'})
            require(entry['availability'] in ['available', 'unavailable', 'retired'])
            require(isinstance(entry['id'], str) and re.fullmatch(r'[a-z][a-z0-9-]{0,99}', entry['id']))
            require(isinstance(entry['version'], str) and re.fullmatch(r'\d+\.\d+\.\d+', entry['version']))
            key = (entry['id'], entry['version'])
            require(key not in self._entries)
            require(isinstance(entry['files'], list) and len(entry['files']) == 2)
            documents = {}
            for file in entry['files']:
                require(set(file) == {'role', 'path', 'sha256'})
                role = file['role']
                require(role in ['descriptor', 'snapshot'] and role not in documents)
                require(isinstance(file['path'], str) and '\\' not in file['path'])
                parts = Path(file['path'])
                require(not parts.is_absolute() and '..' not in parts.parts)
                path = (self.base / parts).resolve()
                require(path.is_relative_to(self.base.resolve()))
                require(parts.as_posix() == f'{key[0]}/{key[1]}/{role}.json')
                raw = self._read(path)
                require(hashlib.sha256(raw).hexdigest() == file['sha256'])
                documents[role] = strict_json(raw)
            descriptor, snapshot = documents['descriptor'], documents['snapshot']
            descriptor_validator.validate(descriptor)
            snapshot_validator.validate(snapshot)
            require((descriptor['id'], descriptor['version']) == key)
            require(snapshot['composition']['template'] == {'id': key[0], 'version': key[1]})
            require(snapshot['presentation']['theme'] in descriptor['compatible_themes'])
            require(snapshot['presentation']['theme'] == {'id': 'studio-neutral', 'version': '1.0.0'})
            # Available bundles must have an implemented renderer layout/category.
            require(entry['availability'] != 'available' or (key[0] in LAYOUTS and descriptor['category'] == key[0] and snapshot['composition']['layout'] == LAYOUTS[key[0]]))
            require(entry['availability'] != 'available' or all(s['variant'] in LAYOUT_VARIANTS[snapshot['composition']['layout']] for s in snapshot['composition']['sections']))
            validate_snapshot(snapshot)
            descriptor['availability'] = entry['availability']
            self._entries[key] = {'descriptor': descriptor, 'snapshot': snapshot, 'theme': theme}

    def catalogue(self, category=None, availability='available'):
        items = [v['descriptor'] for v in self._entries.values() if v['descriptor']['availability'] == availability and (category is None or v['descriptor']['category'] == category)]
        items.sort(key=lambda x: tuple(map(int, x['version'].split('.'))), reverse=True)
        items.sort(key=lambda x: x['id'])
        return copy.deepcopy(items)

    def get(self, template_id, version):
        entry = self._entries.get((template_id, version))
        return copy.deepcopy(entry) if entry else None
