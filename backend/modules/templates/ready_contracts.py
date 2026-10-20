"""E0702 offline contracts. No models, settings, DB, API, renderer or storage."""
import copy
import json
import math
import re
from jsonschema import FormatChecker
from .hero_contracts import ROOT, schema_validator, contrast_ratio

LIMIT = 262144
CAPABILITIES = {'typed-slots-v2': True, 'ready-renderer-v1': False,
                'safe-media-v1': False, 'manual-publication-v1': False}
ROLES = ('descriptor', 'snapshot', 'style-policy', 'fonts', 'responsive', 'demo-content')


class ReadyContractError(ValueError):
    def __init__(self):
        super().__init__('Invalid or unsupported ready template contract.')


def require(value):
    if not value:
        raise ReadyContractError()


def bounded(value, depth=0):
    """Shared conservative byte accounting, not language-specific JSON float output."""
    require(depth <= 32)
    if value is None:
        return 4
    if type(value) is bool:
        return 5
    if isinstance(value, str):
        # Conservative shared bound includes potential JSON escaping (six bytes/codepoint).
        require(not any(0xD800 <= ord(c) <= 0xDFFF for c in value))
        return 2 + sum(max(6 if ord(c) < 32 or c in '\\"' else 0, len(c.encode('utf-8'))) for c in value)
    if type(value) in (float, int):
        require(math.isfinite(value) and abs(value) <= 9007199254740991)
        return 24
    if type(value) is list:
        return 2 + len(value) + sum(bounded(v, depth+1) for v in value)
    require(type(value) is dict and all(type(k) is str for k in value))
    return 2 + len(value)*2 + sum(bounded(k, depth+1)+bounded(v, depth+1) for k, v in value.items())


def check_schema(name, value):
    require(bounded(value) <= LIMIT)
    try:
        schema_validator('ready/'+name).evolve(format_checker=FormatChecker(formats=['uuid'])).validate(value)
    except Exception:
        raise ReadyContractError() from None


def nonblank(value):
    return bool(re.sub(r'[\x09-\x0D\x20\x85\xA0\u1680\u2000-\u200A\u2028\u2029\u202F\u205F\u3000\uFEFF]', '', value))


def safe_link(target):
    kind = target['kind']
    if kind == 'external':
        url = target['url']
        require(url.isascii() and not any(ord(c) <= 32 or ord(c) == 127 for c in url) and re.fullmatch(r'https://([A-Za-z0-9][A-Za-z0-9.-]*)(?::([0-9]{1,5}))?([/?#][^\s\\]*)?', url))
        match = re.fullmatch(r'https://([A-Za-z0-9][A-Za-z0-9.-]*)(?::([0-9]{1,5}))?([/?#][^\s\\]*)?', url)
        require(all(x and len(x) <= 63 and not x.startswith('-') and not x.endswith('-') for x in match[1].split('.')))
        require(not match[2] or 1 <= int(match[2]) <= 65535)
        require(not re.search(r'%(?![0-9A-Fa-f]{2})', url))
    elif kind == 'email':
        require(re.fullmatch(r'[A-Za-z0-9._+-]{1,64}@[A-Za-z0-9.-]+\.[A-Za-z]{2,63}', target['address']))
        local, host = target['address'].split('@')
        require(not local.startswith('.') and not local.endswith('.') and '..' not in local)
        require(all(x and len(x) <= 63 and not x.startswith('-') and not x.endswith('-') for x in host.split('.')))
    else:
        require(kind == 'section')


class ReadyValidator:
    def __init__(self, bundle):
        try:
            self.bundle = copy.deepcopy(bundle)
            for role, schema in [('descriptor','descriptor.v2.json'),('style-policy','style-policy.v1.json'),
                                 ('fonts','fonts.v1.json'),('responsive','responsive.v1.json'),('demo-content','content.v2.json')]:
                check_schema(schema, self.bundle[role])
            self.descriptor = self.bundle['descriptor']
            require(set(self.bundle) == set(ROLES))
            d = self.descriptor
            require(d['template'] == {'id':'creative-editorial','version':'1.0.0'})
            require(d['renderer'] == {'id':'ready-portfolio','version':'1.0.0'} and d['status'] == 'draft')
            require(d['required_capabilities'] == list(CAPABILITIES))
            require(d['customization_policy'] == self.bundle['style-policy']['reference'] == {'id':'creative-editorial-style','version':'1.0.0'})
            for palette in self.bundle['style-policy']['palettes'].values():
                require(all(re.fullmatch(r'#[0-9A-Fa-f]{6}', color) for color in palette.values()))
                require(all(contrast_ratio(palette['text'],palette[k]) >= 4.5 for k in ('background','surface')))
                require(contrast_ratio(palette['accent'],palette['surface']) >= 4.5)
            require(d['publication_policy'] == {'required_text_slots':['identity_name','hero_title'],
                'project_slot':'selected_projects','min_real_projects':1,'contact_slots':['contact_link','socials']})
            self.validate(self.bundle['snapshot'])
            demonstration = copy.deepcopy(self.bundle['snapshot'])
            demonstration['content'] = self.bundle['demo-content']
            self.validate(demonstration)
        except Exception:
            raise ReadyContractError() from None

    def validate(self, document):
        try:
            check_schema('snapshot.v3.json', document)
            b, d = self.bundle, self.descriptor
            # Composition is copied, not user-authored. Validate canonical bindings, not merely shape.
            expected = [('navigation','creative-navigation.v1',{'identity':'identity_name','logo':'brand_logo'}),
                ('hero','creative-hero.v1',{'title':'hero_title','subtitle':'hero_subtitle','portrait':'hero_portrait','cta':'hero_cta'}),
                ('about','creative-about.v1',{'heading':'about_heading','body':'about_body'}),
                ('projects','creative-projects.v1',{'heading':'projects_heading','items':'selected_projects'}),
                ('contact','creative-contact.v1',{'heading':'contact_heading','link':'contact_link','socials':'socials'}),
                ('footer','creative-footer.v1',{'note':'footer_note'})]
            composition = document['composition']
            require(composition['template'] == d['template'])
            require(composition['sections'] == [{'id':i,'variant':v,'slot_bindings':s} for i,v,s in expected])
            require(composition['responsive_profile'] == b['responsive']['reference'])
            require(set(document['content']['slots']) == set(d['slots']))
            slots = document['content']['slots']
            links, images, project_ids = [], [], set()
            for key, definition in d['slots'].items():
                value = slots[key]
                require(value['type'] == definition['type'])
                if value['type'] == 'text':
                    require(len(value['value']) <= definition['max_length'])
                elif value['type'] == 'rich_text':
                    text = ''.join(c['text'] for block in value['blocks'] for c in block['children'])
                    require(len(text) <= definition['max_length'] and bounded(value) <= 12288)
                elif value['type'] in ('image','logo'):
                    if value['value'] is not None:
                        images.append((value['value'], value['type']))
                elif value['type'] == 'link':
                    if value['target'] is not None:
                        links.append(value['target'])
                elif value['type'] == 'project_list':
                    require(len(value['items']) <= definition['max_items'])
                    for p in value['items']:
                        require(p['id'] not in project_ids)
                        project_ids.add(p['id'])
                        if p['cover'] is not None:
                            images.append((p['cover'], 'cover'))
                        if p['target'] is not None:
                            require(p['target']['kind'] == 'external')
                            links.append(p['target'])
                elif value['type'] == 'social_links':
                    require(len(value['items']) <= definition['max_items'])
                    networks = set()
                    domains = {'linkedin':'linkedin.com','behance':'behance.net','dribbble':'dribbble.com','github':'github.com'}
                    for item in value['items']:
                        require(item['network'] not in networks and item['target']['kind'] == 'external')
                        networks.add(item['network']); links.append(item['target'])
                        if item['network'] != 'other':
                            from urllib.parse import urlsplit
                            host = urlsplit(item['target']['url']).hostname
                            domain = domains[item['network']]
                            require(host == domain or host.endswith('.'+domain))
            visible = {'navigation','hero','footer'}
            if slots['about_body']['blocks'] and any(nonblank(c['text']) for p in slots['about_body']['blocks'] for c in p['children']): visible.add('about')
            if any(nonblank(p['title']) for p in slots['selected_projects']['items']): visible.add('projects')
            if (slots['contact_link']['target'] is not None and nonblank(slots['contact_link']['label'])) or any(nonblank(s['label']) for s in slots['socials']['items']): visible.add('contact')
            for target in links:
                safe_link(target)
                if target['kind'] == 'section': require(target['section_id'] in visible)
            for image, kind in images:
                require(not image['decorative'])  # No decorative user-image slots in this template.
            style = b['style-policy']; presentation = document['presentation']
            require(presentation['style_policy'] == style['reference'])
            require(presentation['defaults'] == b['snapshot']['presentation']['defaults'])
            overrides = document['customization']['style_overrides']
            palette = copy.deepcopy(style['palettes'][overrides.get('palette_id', presentation['defaults']['palette_id'])])
            palette.update(overrides.get('colors', {}))
            require(all(re.fullmatch(r'#[0-9A-Fa-f]{6}', color) for color in palette.values()))
            font = overrides.get('font_ref', presentation['defaults']['font_ref'])
            require(font in style['allowed_font_refs'] and any(f['reference'] == font for f in b['fonts']['fonts']))
            for background in ('background','surface'):
                require(contrast_ratio(palette['text'],palette[background]) >= 4.5)
            require(contrast_ratio(palette['accent'],palette['surface']) >= 4.5)
            return {'schema_version':3,'visible_sections':[i for i,_,_ in expected if i in visible],
                    'palette':palette,'font_ref':copy.deepcopy(font)}
        except Exception:
            raise ReadyContractError() from None

    def readiness(self, document, facts):
        """Content assessment only. Facts supplied by trusted future services, never request data."""
        self.validate(document)
        check_schema('assessment-facts.v1.json', facts)
        slots = document['content']['slots']; errors = []
        for key in self.descriptor['publication_policy']['required_text_slots']:
            if not nonblank(slots[key]['value']): errors.append('required:'+key)
        verified = facts.get('verified_user_project_ids', [])
        if not facts.get('account_id') or not any(p['id'] in verified and nonblank(p['title']) for p in slots['selected_projects']['items']): errors.append('real_project_required')
        contact = slots['contact_link']['target']
        if not (contact and contact['kind'] in ('email','external') and nonblank(slots['contact_link']['label'])) and not any(nonblank(s['label']) for s in slots['socials']['items']): errors.append('contact_required')
        assets = []
        for value in slots.values():
            if value['type'] in ('image','logo') and value['value'] is not None:
                assets.append(value['value']['asset_id'])
                if not nonblank(value['value']['alt']): errors.append('alt_required:'+value['value']['asset_id'])
            if value['type'] == 'project_list':
                for p in value['items']:
                    if p['cover'] is not None:
                        assets.append(p['cover']['asset_id'])
                        if not nonblank(p['cover']['alt']): errors.append('alt_required:'+p['cover']['asset_id'])
        for identity in sorted(set(assets)):
            asset = facts.get('assets', {}).get(identity)
            if not asset or not facts.get('account_id') or asset.get('account_id') != facts['account_id'] or asset.get('state') != 'ready' or asset.get('rights_confirmed') is not True:
                errors.append('media_unresolved:'+identity)
        return {'content_ready':not errors,'publication_enabled':False,'errors':errors}
