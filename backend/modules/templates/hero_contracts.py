"""Offline E.02 contracts. Not imported by views, models or the active registry.

Schema validity/declaration is deliberately NOT renderability or write readiness.
Override resolution belongs to E.03; no persistence, conversion or rendering here.
"""
import copy
import json
import re
from pathlib import Path
from urllib.parse import unquote, urlparse

from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource

ROOT = Path(__file__).resolve().parents[3]
LIMIT = 256 * 1024
LAYOUTS = frozenset(('centered', 'split-screen', 'fullscreen', 'typographic',
                     'asymmetric', 'product-showcase', 'bento-grid'))
APPEARANCES = frozenset(('palette', 'solid', 'gradient', 'system-sans', 'flat', 'glass'))


class HeroContractError(ValueError):
    """Generic public error: never includes documents, filesystem paths or secrets."""


def require(value):
    if not value:
        raise HeroContractError('Invalid or unsupported Hero contract.')


def read_json(path):
    raw = path.read_bytes()
    require(len(raw) <= LIMIT)
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result)
            result[key] = value
        return result
    return json.loads(raw.decode('utf-8'), object_pairs_hook=pairs,
                      parse_constant=lambda _: require(False))


def schema_validator(relative, root=ROOT):
    """Local-only, portable file references; no network schema resolution."""
    base = (Path(root) / 'contracts/schemas').resolve()
    def retrieve(uri):
        parsed = urlparse(uri)
        require(parsed.scheme == 'file' and not parsed.netloc and not parsed.query and not parsed.fragment)
        text = unquote(parsed.path)
        if re.match(r'^/[A-Za-z]:/', text):
            text = text[1:]
        path = Path(text).resolve()
        require(path.is_relative_to(base))
        return Resource.from_contents(read_json(path))
    path = (base / relative).resolve()
    require(path.is_relative_to(base))
    schema = read_json(path)
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator({'$ref': path.as_uri()},
        registry=Registry(retrieve=retrieve), format_checker=FormatChecker())


def validate_schema(relative, document, root=ROOT):
    try:
        require(len(json.dumps(document, ensure_ascii=False, allow_nan=False).encode('utf-8')) <= LIMIT)
        schema_validator(relative, root).validate(document)
    except Exception:
        raise HeroContractError('Invalid or unsupported Hero contract.') from None


def contrast_ratio(first, second):
    def luminance(color):
        require(isinstance(color, str) and re.fullmatch(r'#[0-9A-Fa-f]{6}', color))
        channels = [int(color[i:i+2], 16) / 255 for i in (1, 3, 5)]
        linear = [x / 12.92 if x <= .04045 else ((x + .055) / 1.055) ** 2.4 for x in channels]
        return sum(x*w for x, w in zip(linear, (.2126, .7152, .0722)))
    light, dark = sorted((luminance(first), luminance(second)), reverse=True)
    return (light + .05) / (dark + .05)


def validate_appearance(appearance, complete=False):
    """Validate explicit values, NOT an override merger.

    Complete effective appearances must be checked again by E.03 after resolution.
    The first contract requires an opaque text surface even for glass/gradients.
    Glass is decorative only; it must not make the text surface translucent.
    """
    palette = appearance.get('palette', {})
    if complete:
        require(set(palette) == {'text', 'surface', 'accent'})
    if 'surface' in palette:
        for key in ('text', 'accent'):
            if key in palette:
                require(contrast_ratio(palette[key], palette['surface']) >= 4.5)
    background = appearance.get('background', {})
    if background.get('kind') == 'gradient':
        positions = [s['position'] for s in background['stops']]
        require(positions == sorted(set(positions)))


class HeroCapabilities:
    def __init__(self, root=ROOT, document=None, *, text_layouts=False):
        self.root = Path(root)
        try:
            value = copy.deepcopy(document) if document is not None else read_json(self.root/'contracts/hero/capabilities.v1.json')
            validate_schema('hero/capabilities.v1.json', value, self.root)
            for group, expected in [('layouts', LAYOUTS), ('appearance', APPEARANCES), ('behaviors', {'none'})]:
                entries = value[group]
                require(len(entries) == len(expected) and {e['id'] for e in entries} == expected)
                require(all(e['version'] == '1.0.0' for e in entries))
                # E.02 has no modular implementation, even for the two legacy layouts.
                require(all(not e['implemented'] and not e['selectable'] for e in entries))
                for entry in entries:
                    expected_needs = (['content-v2', 'media-assets'] if group == 'layouts' and entry['id'] == 'product-showcase'
                                      else ['content-v2'] if group == 'layouts' and entry['id'] == 'bento-grid' else [])
                    require(entry['requires'] == expected_needs)
            require(type(text_layouts) is bool)
            self._text_layouts = []
            if text_layouts:
                profile = read_json(self.root/'contracts/hero/text-layouts.v1.json')
                validate_schema('hero/text-layouts.v1.json', profile, self.root)
                require(profile == {'schema_version':1, 'id':'text-layouts', 'version':'1.0.0',
                    'layouts':[{'id':i, 'version':'1.1.0', 'requires':['content-v1']}
                               for i in ('product-showcase', 'bento-grid')]})
                self._text_layouts = profile['layouts']
            self._document = value
        except Exception:
            raise HeroContractError('Invalid or unsupported Hero contract.') from None

    def document(self):
        return copy.deepcopy(self._document)

    def declared_layout(self, identity):
        require(any(e['id'] == identity['id'] and e['version'] == identity['version'] for e in [*self._document['layouts'], *self._text_layouts]))

    def require_content_compatible(self, identity):
        self.declared_layout(identity)
        if identity['id'] in {'product-showcase', 'bento-grid'}:
            require(any(e['id'] == identity['id'] and e['version'] == identity['version']
                        for e in self._text_layouts))

    def selectable_layouts(self):
        return []  # Deliberately no runtime feature activation in E.02.

    def require_selectable(self, identity):
        self.declared_layout(identity)
        raise HeroContractError('Hero capability is not selectable.')

    def validate_hero(self, document):
        validate_schema('hero/hero-config.v1.json', document, self.root)
        if 'layout' in document:
            self.declared_layout(document['layout'])
        if 'appearance' in document:
            validate_appearance(document['appearance'])

    def validate_design(self, document):
        """Contract checks only. No resolution/conversion or readiness to save."""
        validate_schema('templates/documents/snapshot.v2.json', document, self.root)
        # Reuse historical section/order invariants without changing the document.
        # This is NOT a converter and does not resolve effective Hero values.
        from .registry import validate_snapshot, RegistryInvalid, LAYOUT_VARIANTS
        try:
            validate_snapshot(document)
            require(all(s['variant'] in LAYOUT_VARIANTS[document['composition']['layout']]
                        for s in document['composition']['sections']))
        except (RegistryInvalid, KeyError):
            raise HeroContractError('Invalid or unsupported Hero contract.') from None
        sections = {s['id']: s for s in document['composition']['sections']}
        presentations = {s['section_id']: s for s in document['presentation']['sections']}
        for identity, section in sections.items():
            presentation = presentations[identity]
            require(('hero' in presentation) == (section['type'] == 'hero'))
            if section['type'] != 'hero':
                continue
            hero = section['hero']
            self.declared_layout(hero['layout'])
            self.require_content_compatible(hero['layout'])
            allowed = hero['policy']['layouts']
            require(len({(e['id'], e['version']) for e in allowed}) == len(allowed))
            for entry in allowed:
                self.declared_layout(entry)
            require({k: hero['layout'][k] for k in ('id', 'version')} in allowed)
            validate_appearance(presentation['hero']['appearance'], complete=True)
            for settings in [hero['layout']['settings'], *hero['layout'].get('responsive', {}).values()]:
                require(all(v in section['presentation_policy'][k] for k, v in settings.items()))
        for override in document['customization']['sections']:
            if 'hero' not in override:
                continue
            source = sections[override['section_id']]
            require(source['type'] == 'hero')
            self.validate_hero(override['hero'])
            layout = override['hero'].get('layout')
            if layout:
                self.require_content_compatible(layout)
                require({k: layout[k] for k in ('id', 'version')} in source['hero']['policy']['layouts'])
                for settings in [layout.get('settings', {}), *layout.get('responsive', {}).values()]:
                    require(all(v in source['presentation_policy'][k] for k, v in settings.items()))
