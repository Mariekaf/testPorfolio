"""Pure converter tests: no Django settings/database initialization."""
import copy
import json
import unittest
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch
from modules.templates.hero_contracts import ROOT, HeroContractError
from modules.templates.hero_conversion import convert_v1_to_v2
from modules.templates.hero_resolution import resolve_heroes


class ConversionTests(unittest.TestCase):
    def snapshot(self, name='minimal'):
        return json.loads((ROOT/f'contracts/templates/{name}/1.0.0/snapshot.json').read_text(encoding='utf-8'))

    def test_both_versions_preserve_content_order_visibility_and_independence(self):
        for name in ('minimal','editorial'):
            source=self.snapshot(name);before=copy.deepcopy(source)
            target=convert_v1_to_v2(source)
            self.assertEqual(source,before)
            self.assertEqual(target['content'],source['content'])
            self.assertEqual(target['composition']['template'],source['composition']['template'])
            self.assertEqual(target['presentation']['theme'],source['presentation']['theme'])
            self.assertIsNone(target['experience'])
            result=resolve_heroes(target)
            self.assertEqual(result['heroes'][0]['layout']['id'],'centered' if name=='minimal' else 'split-screen')
            target['content']['sections'][0]['data']['title']='changed'
            self.assertEqual(source,before)

    def test_legacy_hero_overrides_move_without_becoming_defaults(self):
        source=self.snapshot();source['customization']['sections']=[{'section_id':'hero','presentation':{'spacing':'airy'}},{'section_id':'about','visible':False}]
        target=convert_v1_to_v2(source)
        override=target['customization']['sections'][0]
        self.assertNotIn('presentation',override)
        self.assertEqual(override['hero']['layout']['settings'],{'spacing':'airy'})
        self.assertEqual(resolve_heroes(target)['heroes'][0]['layout']['settings']['mobile']['spacing'],'airy')
        self.assertEqual(target['composition']['sections'][0]['hero']['layout']['settings'],source['presentation']['sections'][0]['settings'])
        self.assertEqual(target['customization']['sections'][1],source['customization']['sections'][1])

    def test_invalid_or_repeated_conversion_fails_without_mutation(self):
        source=self.snapshot();before=copy.deepcopy(source)
        for version in ('2.0.0',None):
            with self.assertRaises(HeroContractError):convert_v1_to_v2(source,version)
        with self.assertRaises(HeroContractError):convert_v1_to_v2(convert_v1_to_v2(source))
        self.assertEqual(source,before)

    def test_never_queries_catalogue(self):
        with patch('modules.templates.registry.TemplateRegistry',side_effect=AssertionError('Catalogue accessed')):
            convert_v1_to_v2(self.snapshot())

    def test_isolated_helper_refuses_without_execution_authorization(self):
        with tempfile.TemporaryDirectory() as folder:
            output=Path(folder)/'must-not-be-created'
            result=subprocess.run([sys.executable,'-B',str(ROOT/'scripts/verification/run_e04_isolated.py'),
                '--engine','native','--output',str(output)],capture_output=True,text=True)
            self.assertNotEqual(result.returncode,0)
            self.assertFalse(output.exists())
