"""Pure E.03 tests. No Django initialization, settings or database access."""
import copy
import hashlib
import json
import subprocess
import unittest
from pathlib import Path

from modules.templates.hero_contracts import ROOT, HeroCapabilities, HeroContractError
from modules.templates.hero_resolution import resolve_heroes, reset_hero_override

FIXTURE=json.loads((ROOT/'contracts/fixtures/hero/resolution.v1.json').read_text(encoding='utf-8'))


def prepare(case):
    result=copy.deepcopy(FIXTURE['base_design'])
    for change in case['changes']:
        keys=change['path'].split('/')[1:]
        node=result
        for key in keys[:-1]:
            node=node[int(key)] if isinstance(node,list) else node[key]
        key=int(keys[-1]) if isinstance(node,list) else keys[-1]
        if change.get('remove'):
            del node[key]
        elif isinstance(node,list) and key==len(node):
            node.append(copy.deepcopy(change['value']))
        else:
            node[key]=copy.deepcopy(change['value'])
    return result


def run_case(case):
    document=prepare(case)
    before=copy.deepcopy(document)
    reset_document=None
    try:
        if 'reset' in case:
            reset_document=reset_hero_override(document,case['reset']['section_id'],case['reset']['path'])
        result=resolve_heroes(reset_document if reset_document is not None else document)
        return {'id':case['id'],'result':result,**({'reset_document':reset_document} if 'reset' in case else {})}
    except HeroContractError:
        return {'id':case['id'],'error':True}
    finally:
        if document!=before:
            raise AssertionError('Resolver mutated its input.')


class ResolutionCases(unittest.TestCase):
    pass


def make_test(case):
    def test(self):
        outcome=run_case(case)
        if case.get('error'):
            self.assertEqual(outcome,{'id':case['id'],'error':True})
        else:
            self.assertEqual(outcome['result'],case['expected'])
            if 'reset' in case:
                after=outcome['reset_document']
                self.assertEqual(reset_hero_override(after,case['reset']['section_id'],case['reset']['path']),after)
    return test


for case in FIXTURE['cases']:
    setattr(ResolutionCases,'test_'+case['id'].replace('-','_'),make_test(case))


class ResolutionBoundaries(unittest.TestCase):
    def test_v1_sources_match_approved_reference_with_only_checkout_crlf_equivalence(self):
        reference=json.loads((ROOT/'contracts/fixtures/hero/v1-reference.v1.json').read_text(encoding='utf-8'))
        for name, expected in reference['files'].items():
            raw=(ROOT/name).read_bytes()
            raw.decode('utf-8',errors='strict')
            self.assertEqual(hashlib.sha256(raw.replace(b'\r\n',b'\n')).hexdigest(),expected,name)

    def test_actual_typescript_python_parity_including_reset_documents(self):
        result=subprocess.run(['node','packages/content-contracts/test/hero-resolution-driver.ts'],
            cwd=ROOT,check=True,capture_output=True,text=True,encoding='utf-8',timeout=60)
        self.assertEqual(json.loads(result.stdout),[run_case(c) for c in FIXTURE['cases']])

    def test_results_and_breakpoints_are_independent(self):
        document=copy.deepcopy(FIXTURE['base_design'])
        before=copy.deepcopy(document)
        first=resolve_heroes(document)
        second=resolve_heroes(document)
        first['heroes'][0]['content']['title']='changed'
        first['heroes'][0]['layout']['settings']['mobile']['spacing']='airy'
        first['heroes'][0]['appearance']['palette']['text']='#123456'
        self.assertEqual(second,FIXTURE['cases'][0]['expected'])
        self.assertEqual(first['heroes'][0]['layout']['settings']['desktop']['spacing'],'normal')
        self.assertEqual(document,before)
        self.assertEqual(resolve_heroes(document),second)

    def test_runtime_capabilities_stay_unavailable(self):
        before=HeroCapabilities().document()
        resolve_heroes(FIXTURE['base_design'])
        self.assertEqual(HeroCapabilities().document(),before)
        self.assertEqual(HeroCapabilities().selectable_layouts(),[])

    def test_no_catalogue_read_and_no_v1_conversion(self):
        from unittest.mock import patch
        from modules.templates.registry import TemplateRegistry
        with patch.object(TemplateRegistry,'__init__',side_effect=AssertionError('Catalogue must not be read')):
            resolve_heroes(FIXTURE['base_design'])
        v1=json.loads((ROOT/'contracts/templates/minimal/1.0.0/snapshot.json').read_text(encoding='utf-8'))
        with self.assertRaises(HeroContractError):
            resolve_heroes(v1)

    def test_oversize_and_non_json_inputs(self):
        for value in [None,float('nan'),{},[]]:
            with self.assertRaises(HeroContractError):
                resolve_heroes(value)
        document=copy.deepcopy(FIXTURE['base_design'])
        document['content']['sections'][0]['data']['title']='a'*262145
        with self.assertRaises(HeroContractError):
            resolve_heroes(document)


if __name__=='__main__':
    unittest.main()
