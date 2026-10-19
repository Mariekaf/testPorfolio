"""E.03 pure Hero resolution: no model, settings, database, renderer or conversion."""
import copy

from .hero_contracts import HeroCapabilities, HeroContractError, validate_appearance, require

SETTINGS = ('spacing', 'alignment', 'emphasis')
BREAKPOINTS = ('mobile', 'tablet', 'desktop')
RESET_PATHS = {(), ('layout',), ('appearance',), ('behavior',),
               ('layout', 'settings'), ('layout', 'responsive'),
               ('appearance', 'palette'), ('appearance', 'typography'),
               ('appearance', 'background'), ('appearance', 'surface')}
RESET_PATHS |= {('layout', 'settings', key) for key in SETTINGS}
for breakpoint in ('tablet', 'desktop'):
    RESET_PATHS.add(('layout', 'responsive', breakpoint))
    RESET_PATHS |= {('layout', 'responsive', breakpoint, key) for key in SETTINGS}
RESET_PATHS |= {('appearance', 'palette', key) for key in ('text', 'surface', 'accent')}
RESET_PATHS |= {('appearance', 'typography', key) for key in ('family', 'scale')}


def resolve_heroes(document):
    """Resolve a Design v2 into fresh effective Hero configurations, or fail closed."""
    try:
        return _resolve_heroes(document)
    except Exception:
        raise HeroContractError('Invalid or unsupported Hero contract.') from None


def _resolve_heroes(document):
    """Return a fresh effective configuration for every Hero, including hidden ones.

    Contract validity is not renderability: the capability registry stays inactive.
    Only local copied defaults are read. v1 is rejected, never converted.
    """
    registry = HeroCapabilities()
    registry.validate_design(document)
    presentations = {s['section_id']: s for s in document['presentation']['sections']}
    contents = {s['section_id']: s for s in document['content']['sections']}
    overrides = {s['section_id']: s for s in document['customization']['sections']}
    sections = {s['id']: s for s in document['composition']['sections']}
    order = document['customization'].get('section_order', list(sections))
    heroes = []
    for identity in order:
        section = sections[identity]
        if section['type'] != 'hero':
            continue
        source = section['hero']['layout']
        presentation = presentations[identity]
        override = overrides.get(identity, {})
        hero = override.get('hero', {})
        local_layout = hero.get('layout', {})
        appearance = copy.deepcopy(presentation['hero']['appearance'])
        for key, value in hero.get('appearance', {}).items():
            if key in ('palette', 'typography'):
                appearance[key].update(copy.deepcopy(value))
            else:
                appearance[key] = copy.deepcopy(value)
        layout = {key: local_layout.get(key, source[key]) for key in ('id', 'version')}
        settings = {}
        base = {**presentation['settings'], **override.get('presentation', {}),
                **source['settings'], **local_layout.get('settings', {})}
        for breakpoint in BREAKPOINTS:
            values = dict(base)
            if breakpoint != 'mobile':
                values.update(source.get('responsive', {}).get(breakpoint, {}))
                values.update(local_layout.get('responsive', {}).get(breakpoint, {}))
            require(all(v in section['presentation_policy'][k] for k, v in values.items()))
            settings[breakpoint] = values
        behavior = copy.deepcopy(hero.get('behavior', {'kind': 'none'}))
        # Revalidate a complete effective Hero, including all responsive branches.
        registry.validate_hero({'schema_version': 1, 'layout': {**layout,
            'settings': settings['mobile'], 'responsive': {b:settings[b] for b in ('tablet', 'desktop')}},
            'appearance':appearance, 'behavior':behavior})
        validate_appearance(appearance, complete=True)
        heroes.append({'section_id':identity, 'visible':override.get('visible', section['visible']),
                       'content':copy.deepcopy(contents[identity]['data']),
                       'layout':{**layout, 'settings':settings}, 'appearance':appearance,
                       'behavior':behavior})
    return {'schema_version':1, 'design_schema_version':2, 'heroes':heroes}


def reset_hero_override(document, section_id, path=()):
    """Return a validated copy after deleting an allowed local Hero override key."""
    try:
        return _reset_hero_override(document, section_id, path)
    except Exception:
        raise HeroContractError('Invalid or unsupported Hero contract.') from None


def _reset_hero_override(document, section_id, path):
    """Return a copied design with an allowed customization key removed.

    Paths are relative to sections[].hero. Empty path removes that Hero override.
    Reset of an already absent allowed key is idempotent; null is never written.
    Background/surface and layout identity pairs reset atomically.
    """
    registry = HeroCapabilities()
    registry.validate_design(document)
    require(isinstance(path, (list, tuple)) and all(isinstance(k, str) for k in path))
    path = tuple(path)
    require(path in RESET_PATHS)
    require(any(s['id'] == section_id and s['type'] == 'hero' for s in document['composition']['sections']))
    result = copy.deepcopy(document)
    override = next((s for s in result['customization']['sections'] if s['section_id'] == section_id), None)
    if override is not None and 'hero' in override:
        if not path:
            del override['hero']
        else:
            current = override['hero']
            parents = []
            for key in path[:-1]:
                if key not in current:
                    break
                parents.append((current, key))
                current = current[key]
            else:
                current.pop(path[-1], None)
                for parent, key in reversed(parents):
                    if not parent[key]:
                        del parent[key]
    # A reset is also refused if restoring inherited values breaks contrast/policy.
    resolve_heroes(result)
    return result
