"""Explicit, pure converter. Never called from reads or migration backfills."""
import copy
from .hero_contracts import HeroCapabilities, HeroContractError, validate_schema, read_json, ROOT
from .hero_resolution import resolve_heroes
from .registry import validate_snapshot, LAYOUT_VARIANTS

CONVERTER_VERSION = '1.0.0'


def convert_v1_to_v2(document, converter_version=CONVERTER_VERSION):
    try:
        if converter_version != CONVERTER_VERSION:
            raise HeroContractError()
        validate_schema('templates/documents/snapshot.v1.json', document)
        validate_snapshot(document)
        if any(s['variant'] not in LAYOUT_VARIANTS[document['composition']['layout']] for s in document['composition']['sections']):
            raise HeroContractError()
        result = copy.deepcopy(document)
        result['schema_version'] = 2
        for name in ('composition', 'presentation', 'customization'):
            result[name]['schema_version'] = 2
        theme = read_json(ROOT/'contracts/themes/studio-neutral.v1.json')
        colors = theme['tokens']['light']
        presentations = {s['section_id']: s for s in result['presentation']['sections']}
        overrides = {s['section_id']: s for s in result['customization']['sections']}
        for section in result['composition']['sections']:
            if section['type'] != 'hero':
                continue
            presentation = presentations[section['id']]
            identity = {'hero-centered':'centered', 'hero-split':'split-screen'}[section['variant']]
            section['hero'] = {'schema_version':1,
                'layout':{'id':identity, 'version':'1.0.0', 'settings':copy.deepcopy(presentation['settings'])},
                'policy':{'layouts':[{'id':name, 'version':'1.0.0'} for name in
                    ('centered','split-screen','fullscreen','typographic','asymmetric')],
                    'appearance':True, 'behaviors':['none']}}
            presentation['hero'] = {'schema_version':1, 'appearance':{
                'palette':{'text':colors['text'], 'surface':colors['background'], 'accent':colors['accent']},
                'typography':{'family':'system-sans', 'scale':'balanced'},
                'background':{'kind':'solid', 'color':colors['background']}, 'surface':{'kind':'flat'}}}
            override = overrides.get(section['id'])
            if override and 'presentation' in override:
                # Move legacy Hero settings into their effective v2 override layer.
                # Original defaults remain defaults; reset restores those defaults.
                settings = override.pop('presentation')
                if settings:
                    override['hero'] = {'schema_version':1, 'layout':{
                        'id':identity, 'version':'1.0.0', 'settings':settings}}
        HeroCapabilities().validate_design(result)
        resolve_heroes(result)
        return result
    except Exception:
        raise HeroContractError('Explicit Hero conversion refused.') from None
