"""E0702 entirely offline. Uses only Git fixtures and disposable directories."""
import base64
import copy
import hashlib
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from modules.templates.hero_contracts import ROOT
from modules.templates.ready_contracts import ReadyContractError
from modules.templates.ready_registry import ReadyRegistry, strict_json

FIXTURES = json.loads((ROOT/'contracts/fixtures/ready/validation.v1.json').read_text(encoding='utf-8'))
REGISTRY = ReadyRegistry()
BASE = REGISTRY.get()['bundle']['snapshot']


def prepare(changes):
    result = copy.deepcopy(BASE)
    for change in changes:
        keys = change['path'][1:].split('/')
        node = result
        for key in keys[:-1]:
            if isinstance(node, list):
                node = node[int(key)]
            else:
                node = node.setdefault(key, {})
        node[int(keys[-1]) if isinstance(node, list) else keys[-1]] = copy.deepcopy(change['value'])
    return result


def node(request):
    result = subprocess.run(['node',str(ROOT/'scripts/verification/ready-e0702-driver.mjs')],
        input=json.dumps(request,ensure_ascii=False),encoding='utf-8',capture_output=True,check=True,cwd=ROOT,timeout=30)
    return json.loads(result.stdout)


class ReadyDocumentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.validator = REGISTRY.validator()

    def test_actual_typescript_parity_all_vectors(self):
        request={'cases':[{'document':prepare(c['changes']),'facts':c['facts']} for c in FIXTURES['cases']]}
        actual=node(request)
        self.assertEqual(len(actual),len(FIXTURES['cases']))
        for c,value in zip(FIXTURES['cases'],actual):
            with self.subTest(case=c['id']):
                d=prepare(c['changes'])
                expected={'result':self.validator.validate(d),'readiness':self.validator.readiness(d,c['facts'])} if c['valid'] else {'error':True}
                self.assertEqual(value,expected)

    def test_registry_digest_parity(self):
        entry=REGISTRY.get()
        self.assertEqual(node({'mode':'registry','root':str(ROOT/'contracts/ready-templates')}),
            {'valid':True,'digest':entry['bundle_digest'],'status':'draft'})

    def test_copies_independent(self):
        entry=REGISTRY.get();entry['bundle']['snapshot']['content']['slots']['identity_name']['value']='changed'
        self.assertEqual(REGISTRY.get()['bundle']['snapshot']['content']['slots']['identity_name']['value'],'')
        document=copy.deepcopy(BASE);document['customization']['style_overrides']['colors']={'accent':'#FFFFFF'}
        self.assertEqual(self.validator.validate(document)['palette']['accent'],'#FFFFFF')
        del document['customization']['style_overrides']['colors']
        self.assertEqual(self.validator.validate(document)['palette']['accent'],'#D5EB90')
        with self.assertRaises(ReadyContractError):self.validator.readiness(BASE,{'publication_enabled':True})


def document_test(case):
    def run(self):
        document=prepare(case['changes']);before=copy.deepcopy(document)
        if case['valid']:
            self.validator.validate(document)
            state=self.validator.readiness(document,case['facts'])
            self.assertEqual(state['content_ready'],case['ready']);self.assertFalse(state['publication_enabled'])
        else:
            with self.assertRaises(ReadyContractError):self.validator.validate(document)
        self.assertEqual(document,before)
    return run

for index,case in enumerate(FIXTURES['cases']):setattr(ReadyDocumentTests,f'test_vector_{index:02d}_{case["id"].replace("-","_")}',document_test(case))


class ReadyRegistrySafetyTests(unittest.TestCase):
    def test_strict_json_parity(self):
        for raw in [b'{"x":1,"x":2}',b'{"x":{"a":1,"a":2}}',b'{"a":1,"\\u0061":2}',b'[1,]',b'{"x":NaN}',b'\xef\xbb\xbf{}',b'{"x":"\\ud800"}',b'\xff',b'['*34+b']'*34]:
            with self.subTest(raw=repr(raw)):
                with self.assertRaises(ReadyContractError):strict_json(raw)
                self.assertEqual(node({'mode':'raw','raw':base64.b64encode(raw).decode()}),{'error':True})

    def test_corruption_and_path_guards_match_typescript(self):
        for mutation in ('hash','bytes','digest','duplicate-entry','duplicate-role','missing-file','available','preview','traversal','absolute','backslash','case-collision','unsafe-font','unknown-policy'):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory(prefix='ready-e0702-') as directory:
                target=Path(directory)/'registry';shutil.copytree(ROOT/'contracts/ready-templates',target)
                path=target/'manifest.v2.json';manifest=json.loads(path.read_text(encoding='utf-8'));entry=manifest['entries'][0];file=entry['files'][0]
                if mutation=='hash':file['sha256']='0'*64
                elif mutation=='bytes':file['bytes']+=1
                elif mutation=='digest':entry['bundle_digest']='0'*64
                elif mutation=='duplicate-entry':manifest['entries'].append(copy.deepcopy(entry))
                elif mutation=='duplicate-role':entry['files'][1]['role']=file['role']
                elif mutation=='missing-file':(target/file['path']).unlink()
                elif mutation in ('available','preview'):entry['status']=mutation
                elif mutation=='traversal':file['path']='../outside.json'
                elif mutation=='absolute':file['path']='/outside.json'
                elif mutation=='backslash':file['path']=file['path'].replace('/','\\')
                elif mutation=='case-collision':entry['files'][1]['path']=file['path'].upper()
                else:
                    role='fonts' if mutation=='unsafe-font' else 'descriptor'
                    item=next(x for x in entry['files'] if x['role']==role);p=target/item['path'];value=json.loads(p.read_text(encoding='utf-8'))
                    if role=='fonts':value['fonts'][0]['source']='remote'
                    else:value['slots']['hero_title']['max_length']=9999
                    raw=(json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode('utf-8');p.write_bytes(raw);item.update(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
                    canonical=[{k:f[k] for k in ('path','bytes','sha256')} for f in sorted(entry['files'],key=lambda f:f['path'])]
                    entry['bundle_digest']=hashlib.sha256(json.dumps(canonical,separators=(',',':')).encode()).hexdigest()
                path.write_text(json.dumps(manifest,ensure_ascii=False),encoding='utf-8')
                with self.assertRaises(ReadyContractError):ReadyRegistry(target)
                self.assertEqual(node({'mode':'registry','root':str(target)}),{'error':True})

    def test_symlink_payload_refused(self):
        with tempfile.TemporaryDirectory(prefix='ready-e0702-') as directory:
            root=Path(directory);target=root/'registry';shutil.copytree(ROOT/'contracts/ready-templates',target)
            path=target/'creative-editorial/1.0.0/snapshot.json';outside=root/'outside.json';path.replace(outside)
            try:path.symlink_to(outside)
            except OSError as error:self.skipTest('Environment cannot create symlink: '+type(error).__name__)
            with self.assertRaises(ReadyContractError):ReadyRegistry(target)
            self.assertEqual(node({'mode':'registry','root':str(target)}),{'error':True})
