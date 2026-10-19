"""TPL-001.B: strict registry, real API contract and read-only authorization."""
import copy
import hashlib
import json
import shutil
import tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from django.test import SimpleTestCase
from rest_framework.test import APIRequestFactory, force_authenticate
from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource
from referencing.jsonschema import DRAFT202012
from modules.templates.registry import ROOT, RegistryInvalid, TemplateRegistry, strict_json
from modules.templates.views import TemplateRead

class RegistryTests(SimpleTestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        shutil.copytree(ROOT/'contracts', self.root/'contracts')

    def rewrite(self, role, change, rehash=True):
        base=self.root/'contracts/templates'
        path=base/'minimal/1.0.0'/f'{role}.json'
        document=json.loads(path.read_text());change(document)
        path.write_text(json.dumps(document,ensure_ascii=False)+'\n')
        if rehash:
            manifest=json.loads((base/'manifest.v1.json').read_text())
            file=next(f for e in manifest['entries'] if e['id']=='minimal' for f in e['files'] if f['role']==role)
            file['sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
            (base/'manifest.v1.json').write_text(json.dumps(manifest))

    def manifest(self, change):
        p=self.root/'contracts/templates/manifest.v1.json';data=json.loads(p.read_text());change(data);p.write_text(json.dumps(data))

    def invalid(self):
        with self.assertRaisesRegex(RegistryInvalid,'Invalid template registry'):
            TemplateRegistry(self.root)

    def test_real_bundles_distinct_valid_and_independent_returns(self):
        r=TemplateRegistry();items=r.catalogue()
        self.assertEqual({s['id'] for s in items},{'minimal','editorial'})
        self.assertNotEqual(r.get('minimal','1.0.0')['snapshot']['composition'],r.get('editorial','1.0.0')['snapshot']['composition'])
        items[0]['name']='changed';self.assertNotEqual(r.catalogue()[0]['name'],'changed')
        result=r.get('minimal','1.0.0');result['snapshot']['content']['sections'].clear()
        self.assertTrue(r.get('minimal','1.0.0')['snapshot']['content']['sections'])

    def test_digest_mismatch_fails_even_valid_json(self):
        self.rewrite('descriptor',lambda d:d.update(name='Changed'),False);self.invalid()

    def test_path_traversal_absolute_and_duplicate_entries(self):
        for path in ['../themes/studio-neutral.v1.json','/etc/passwd','minimal\\1.0.0\\snapshot.json']:
            with self.subTest(path=path):
                self.manifest(lambda m:m['entries'][0]['files'][0].update(path=path));self.invalid()
        shutil.copyfile(ROOT/'contracts/templates/manifest.v1.json',self.root/'contracts/templates/manifest.v1.json')
        self.manifest(lambda m:m['entries'].append(copy.deepcopy(m['entries'][0])));self.invalid()

    def test_unknown_schema_and_experience_rejected(self):
        self.rewrite('snapshot',lambda d:d.update(schema_version=2));self.invalid()
        self.rewrite('snapshot',lambda d:d.update(schema_version=1,experience={'engine':'gsap'}));self.invalid()
        # Make a fully self-consistent bundle so only canonical-version policy rejects it.
        for version in ['01.0.0','1.٠.0','1.0.0.0','1'*31+'.0.0']:
            with tempfile.TemporaryDirectory() as folder:
                root=Path(folder);shutil.copytree(ROOT/'contracts',root/'contracts')
                base=root/'contracts/templates';manifest=json.loads((base/'manifest.v1.json').read_text())
                entry=manifest['entries'][0];entry['version']=version
                (base/'minimal/1.0.0').rename(base/'minimal'/version)
                for file in entry['files']:
                    file['path']=f'minimal/{version}/{file["role"]}.json'
                    path=base/file['path'];document=json.loads(path.read_text())
                    if file['role']=='descriptor':document['version']=version
                    else:document['composition']['template']['version']=version
                    path.write_text(json.dumps(document,ensure_ascii=False))
                    file['sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
                (base/'manifest.v1.json').write_text(json.dumps(manifest))
                with self.assertRaises(RegistryInvalid):TemplateRegistry(root)

    def test_invalid_format_and_untrusted_links_rejected(self):
        for link in ['javascript:alert(1)','http://example.test','https://user:pass@example.test','https://example.test/\npath']:
            with self.subTest(link=link):
                def change(d):
                    s=next(s for s in d['content']['sections'] if s['type']=='projects');s['data']['items'][0]['url']=link
                self.rewrite('snapshot',change);self.invalid()

    def test_missing_references_and_wrong_section_type_rejected(self):
        self.rewrite('snapshot',lambda d:d['content']['sections'].pop());self.invalid()
        self.rewrite('snapshot',lambda d:d['composition']['sections'][0].update(variant='contact-panel'));self.invalid()

    def test_valid_variant_for_wrong_layout_is_not_available(self):
        self.rewrite('snapshot',lambda d:d['composition']['sections'][0].update(variant='hero-split'));self.invalid()

    def test_theme_and_identity_mismatch_rejected(self):
        self.rewrite('descriptor',lambda d:d.update(id='other'));self.invalid()
        self.rewrite('descriptor',lambda d:d.update(id='minimal',compatible_themes=[{'id':'studio-neutral','version':'1.0.0'},{'id':'missing','version':'1.0.0'}]));self.invalid()
        self.rewrite('descriptor',lambda d:d.update(compatible_themes=[{'id':'studio-neutral','version':'1.0.0'}],composition_reference={'schema_version':1,'document_id':'30000000-0000-4000-8000-000000000001'}));self.invalid()

    def test_overrides_and_section_order_validated(self):
        def change(d):d['customization']['sections']=[{'section_id':'hero','visible':False}]
        self.rewrite('snapshot',change);self.invalid()
        def change(d):d['customization']={'schema_version':1,'sections':[],'section_order':['contact','hero','projects','about','skills']}
        self.rewrite('snapshot',change);self.invalid()
        def change(d):d['customization']={'schema_version':1,'sections':[{'section_id':'projects','presentation':{'spacing':'airy'}}],'section_order':['hero','about','skills','projects','contact']}
        self.rewrite('snapshot',change);TemplateRegistry(self.root)

    def test_duplicate_keys_oversize_and_no_remote_reference(self):
        for raw in [b'{"schema_version":1,"schema_version":1}',b' '* (256*1024+1)]:
            with self.assertRaises(RegistryInvalid):strict_json(raw)
        p=self.root/'contracts/schemas/templates/documents/snapshot.v1.json'
        d=json.loads(p.read_text());d['properties']['content']={'$ref':'https://example.test/untrusted-schema'};p.write_text(json.dumps(d));self.invalid()

    def test_symlink_outside_bundle_root_rejected(self):
        source=self.root/'contracts/templates/minimal/1.0.0/snapshot.json'
        outside=self.root/'outside.json';outside.write_bytes(source.read_bytes())
        source.unlink()
        try:source.symlink_to(outside)
        except OSError:self.skipTest('Symlink creation unavailable on this platform')
        self.invalid()

    def test_retirement_keeps_bundle_immutable_and_filtering_explicit(self):
        before=(self.root/'contracts/templates/minimal/1.0.0/snapshot.json').read_bytes()
        self.manifest(lambda m:m['entries'][0].update(availability='retired'))
        r=TemplateRegistry(self.root)
        self.assertEqual(len(r.catalogue()),1);self.assertEqual(len(r.catalogue(availability='retired')),1)
        self.assertEqual(before,(self.root/'contracts/templates/minimal/1.0.0/snapshot.json').read_bytes())

class TemplateAPITests(SimpleTestCase):
    def call(self,path='/api/v1/templates',*,template_id=None,version=None,preview=False,auth=True,method='get'):
        req=getattr(APIRequestFactory(),method)(path,format='json')
        if auth:force_authenticate(req,user=SimpleNamespace(is_authenticated=True))
        return TemplateRead.as_view()(req,template_id=template_id,version=version,preview=preview)

    def assert_contract(self,response,path):
        doc=ROOT/'contracts/api/templates.v1.json';api=json.loads(doc.read_text())
        schema=api['paths'][path]['get']['responses'][str(response.status_code)]['content']['application/json']['schema']
        def retrieve(uri):
            target=Path.from_uri(uri).resolve()
            self.assertTrue(target.is_relative_to(ROOT/'contracts'))
            return Resource.from_contents(json.loads(target.read_text()),default_specification=DRAFT202012)
        wrapped={'$ref':doc.as_uri()+'#/paths/'+path.replace('~','~0').replace('/','~1')+'/get/responses/'+str(response.status_code)+'/content/application~1json/schema'}
        Draft202012Validator(wrapped,registry=Registry(retrieve=retrieve),format_checker=FormatChecker()).validate(response.data)
        self.assertIn('no-store',response['Cache-Control'])

    def test_authentication_required_and_no_writes(self):
        anonymous=self.call(auth=False)
        self.assertEqual(anonymous.status_code,401);self.assert_contract(anonymous,'/api/v1/templates')
        for method in ['post','put','patch','delete']:
            response=self.call(method=method);self.assertEqual(response.status_code,405)
            self.assertEqual(response.data['error']['code'],'request_denied');self.assert_contract(response,'/api/v1/templates')

    def test_catalogue_filter_pagination_and_contract(self):
        for query,count in [('',2),('?category=minimal',1),('?availability=retired',0),('?page=2',2)]:
            response=self.call('/api/v1/templates'+query)
            self.assertEqual(response.status_code,200);self.assertEqual(response.data['count'],count)
            self.assert_contract(response,'/api/v1/templates')

    def test_invalid_queries_rejected(self):
        for query in ['?page=0','?page=1&page=2','?category=creative','?availability=fake','?owner=other','?page=٠١']:
            response=self.call('/api/v1/templates'+query);self.assertEqual(response.status_code,400)
            self.assert_contract(response,'/api/v1/templates')

    def test_detail_preview_unknown_and_contracts(self):
        for preview in [False,True]:
            path='/api/v1/templates/{template_id}/versions/{template_version}'+('/preview' if preview else '')
            response=self.call(template_id='editorial',version='1.0.0',preview=preview)
            self.assertEqual(response.status_code,200);self.assert_contract(response,path)
            response=self.call(template_id='editorial',version='999.0.0',preview=preview)
            self.assertEqual(response.status_code,404);self.assert_contract(response,path)

    def test_failure_closed_generic_and_retired_preview(self):
        with patch('modules.templates.views.TemplateRegistry',side_effect=RegistryInvalid('/PRIVATE/SECRET')):
            response=self.call();self.assertEqual(response.status_code,503)
            self.assertNotIn('PRIVATE',str(response.data));self.assert_contract(response,'/api/v1/templates')
        r=TemplateRegistry();entry=r.get('minimal','1.0.0');entry['descriptor']['availability']='retired'
        with patch('modules.templates.views.TemplateRegistry') as constructor:
            constructor.return_value.get.return_value=entry
            response=self.call(template_id='minimal',version='1.0.0',preview=True)
            self.assertEqual(response.status_code,409)
            self.assert_contract(response,'/api/v1/templates/{template_id}/versions/{template_version}/preview')
