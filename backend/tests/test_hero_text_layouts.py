"""E06 textual profile, pure resolution/parity. No Django or SQL initialization."""
import copy
import json
import subprocess
import unittest
from modules.templates.hero_contracts import ROOT, read_json, HeroContractError, HeroCapabilities
from modules.templates.hero_resolution import resolve_heroes, reset_hero_override


def vectors():
    sources = {c['id']: c['design'] for c in read_json(ROOT/'contracts/fixtures/hero/rendering.e06.v1.json')['cases']}
    for case in read_json(ROOT/'contracts/fixtures/hero/text-layouts-parity.v1.json')['cases']:
        document = copy.deepcopy(sources[case['source']])
        for change in case['changes']:
            keys = change['path'].split('/')[1:]
            node = document
            for key in keys[:-1]:
                node = node[int(key)] if isinstance(node, list) else node[key]
            node[keys[-1]] = copy.deepcopy(change['value'])
        yield case, document


class TextLayoutTests(unittest.TestCase):
    def test_common_vectors_and_actual_typescript_parity(self):
        prepared = list(vectors())
        request = [{'document': d, **({'reset': c['reset']} if 'reset' in c else {})} for c, d in prepared]
        before = copy.deepcopy(request)
        process = subprocess.run(['node', str(ROOT/'scripts/verification/hero-e06-parity-driver.mjs')],
            input=json.dumps(request, ensure_ascii=False), encoding='utf-8', capture_output=True,
            check=True, cwd=ROOT, timeout=30)
        typescript = json.loads(process.stdout)
        self.assertEqual(len(typescript), len(prepared))
        for (case, document), actual in zip(prepared, typescript):
            with self.subTest(case=case['id']):
                if not case['valid']:
                    with self.assertRaises(HeroContractError):
                        resolve_heroes(document, text_layouts=True)
                    self.assertEqual(actual, {'error': True})
                else:
                    result_document = reset_hero_override(document, 'hero', case['reset'], text_layouts=True) if 'reset' in case else document
                    expected = {'result': resolve_heroes(result_document, text_layouts=True)}
                    if 'reset' in case:
                        expected['reset_document'] = result_document
                        self.assertNotIn('accent', result_document['customization']['sections'][0]['hero'].get('appearance', {}).get('palette', {}))
                    self.assertEqual(actual, expected)
                    self.assertEqual(expected['result']['heroes'][0]['layout']['id'], case['source'])
        self.assertEqual(request, before)

    def test_frozen_default_profile_still_rejects_textual_variants(self):
        for case in read_json(ROOT/'contracts/fixtures/hero/rendering.e06.v1.json')['cases'][1:]:
            with self.assertRaises(HeroContractError):
                resolve_heroes(case['design'])
            with self.assertRaises(HeroContractError):
                HeroCapabilities().validate_design(case['design'])

    def test_profile_is_explicit_boolean_not_truthy_user_input(self):
        document = read_json(ROOT/'contracts/fixtures/hero/rendering.e06.v1.json')['cases'][0]['design']
        for value in ('yes', 1, None, {}):
            with self.assertRaises(HeroContractError):
                resolve_heroes(document, text_layouts=value)

    def test_explicit_conversion_documents_remain_compatible_with_both_profiles(self):
        from modules.templates.hero_conversion import convert_v1_to_v2
        for name in ('minimal', 'editorial'):
            source = read_json(ROOT/'contracts/templates'/name/'1.0.0/snapshot.json')
            before = copy.deepcopy(source)
            converted = convert_v1_to_v2(source)
            self.assertEqual(resolve_heroes(converted), resolve_heroes(converted, text_layouts=True))
            for identity in ('asymmetric', 'product-showcase', 'bento-grid'):
                document = copy.deepcopy(converted)
                version = '1.0.0' if identity == 'asymmetric' else '1.1.0'
                hero = document['composition']['sections'][0]['hero']
                # Explicit synthetic local policy extension, never a data backfill.
                if {'id': identity, 'version': version} not in hero['policy']['layouts']:
                    hero['policy']['layouts'].append({'id': identity, 'version': version})
                hero['layout'].update(id=identity, version=version)
                document['customization']['sections'] = []
                self.assertEqual(resolve_heroes(document, text_layouts=True)['heroes'][0]['layout']['id'], identity)
                run = subprocess.run(['node', str(ROOT/'scripts/verification/hero-rendering-driver.mjs')],
                    input=json.dumps([document], ensure_ascii=False), encoding='utf-8', capture_output=True,
                    check=True, cwd=ROOT, timeout=30)
                self.assertIn(f'data-hero-layout="{identity}"', json.loads(run.stdout)[0])
            self.assertEqual(source, before)

    def test_tampered_profile_cannot_expand_capabilities(self):
        import tempfile
        import shutil
        from pathlib import Path
        with tempfile.TemporaryDirectory(prefix='e06-contracts-') as directory:
            root = Path(directory)
            shutil.copytree(ROOT/'contracts', root/'contracts')
            path = root/'contracts/hero/text-layouts.v1.json'
            original = read_json(path)
            for edit in ('version', 'requires', 'extra'):
                profile = copy.deepcopy(original)
                if edit == 'version':
                    profile['version'] = '9.0.0'
                elif edit == 'requires':
                    profile['layouts'][0]['requires'] = []
                else:
                    profile['css'] = 'background:red'
                path.write_text(json.dumps(profile, ensure_ascii=False), encoding='utf-8')
                with self.assertRaises(HeroContractError):
                    HeroCapabilities(root=root, text_layouts=True)
