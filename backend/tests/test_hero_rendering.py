"""E05 pure compatibility with explicit E04 conversion. Never connects to SQL."""
import copy
import json
import subprocess
import unittest

from modules.templates.hero_contracts import ROOT, read_json
from modules.templates.hero_conversion import convert_v1_to_v2
from modules.templates.hero_resolution import resolve_heroes


class HeroRenderingCompatibilityTests(unittest.TestCase):
    def check_template(self, name):
        source = read_json(ROOT / 'contracts' / 'templates' / name / '1.0.0' / 'snapshot.json')
        original = copy.deepcopy(source)
        converted = convert_v1_to_v2(source)  # Explicit, pure call; no save or transition.
        variants = []
        for layout in ('centered', 'split-screen', 'fullscreen', 'typographic'):
            document = copy.deepcopy(converted)
            overrides = document['customization']['sections']
            entry = next((s for s in overrides if s['section_id'] == 'hero'), None)
            if entry is None:
                entry = {'section_id': 'hero'}
                overrides.append(entry)
            entry.setdefault('hero', {'schema_version': 1})['layout'] = {'id': layout, 'version': '1.0.0'}
            self.assertEqual(resolve_heroes(document)['heroes'][0]['layout']['id'], layout)
            variants.append(document)
        before = copy.deepcopy(variants)
        run = subprocess.run(['node', str(ROOT / 'scripts/verification/hero-rendering-driver.mjs')],
                             input=json.dumps(variants, ensure_ascii=False), encoding='utf-8',
                             capture_output=True, check=True, cwd=ROOT, timeout=30)
        html = json.loads(run.stdout)
        self.assertEqual(len(html), 4)
        for layout, rendered in zip(('centered', 'split-screen', 'fullscreen', 'typographic'), html):
            self.assertIn(f'data-hero-layout="{layout}"', rendered)
            self.assertIn('<h1 ', rendered)
        self.assertEqual(variants, before)
        self.assertEqual(source, original)
        self.assertEqual(source['schema_version'], 1)
        self.assertEqual(converted['composition']['template'], original['composition']['template'])

    def test_minimal_explicit_e04_conversion_renders_all_four_without_sql(self):
        self.check_template('minimal')

    def test_editorial_explicit_e04_conversion_renders_all_four_without_sql(self):
        self.check_template('editorial')
