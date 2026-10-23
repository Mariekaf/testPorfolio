"""C+D integration on a disposable PostgreSQL test DB; no personal fixtures."""
import copy
import secrets
import uuid
from datetime import timedelta
from unittest.mock import patch
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.db import connection
from django.test import TestCase, TransactionTestCase
from django.utils import timezone
from rest_framework.test import APIClient
from modules.accounts.services import ensure_personal_account
from modules.portfolios.models import Portfolio
from modules.templates.models import PortfolioDesign,TemplateCreationRequest
from modules.templates.registry import TemplateRegistry,RegistryInvalid

class InstanceTests(TestCase):
    def setUp(self):
        self.user=get_user_model().objects.create_user(email='instance@example.test',password=secrets.token_urlsafe(30))
        self.account=ensure_personal_account(self.user)
        # AUTH uses its explicit AuthSession guard: authenticate through real login.
        self.password=secrets.token_urlsafe(30);self.user.set_password(self.password);self.user.save()
        self.client=APIClient(enforce_csrf_checks=True)
        self.send('/api/v1/auth/login',{'email':self.user.email,'password':self.password})

    def send(self,path,data,method='post',tag=None,key=None,client=None):
        client=client or self.client;token=client.get('/api/v1/auth/csrf').json()['csrf_token']
        headers={'HTTP_X_CSRFTOKEN':token}
        if tag is not None:headers['HTTP_IF_MATCH']=tag
        if key is not None:headers['HTTP_IDEMPOTENCY_KEY']=str(key)
        return getattr(client,method)(path,data,format='json',**headers)

    def create(self,template='minimal',key=None,**extra):
        return self.send('/api/v1/portfolios/from-template',{'name':'Mon portfolio','template_id':template,'template_version':'1.0.0',**extra},key=key or uuid.uuid4())

    def design(self,item):return self.client.get('/api/v1/portfolios/'+item['id']+'/design')

    def contract(self,response,path,method):
        import json
        from pathlib import Path
        from jsonschema import Draft202012Validator,FormatChecker
        from referencing import Registry,Resource
        from referencing.jsonschema import DRAFT202012
        from modules.templates.registry import ROOT
        document=ROOT/'contracts/api/template-instances.v1.json'
        def retrieve(uri):
            target=Path.from_uri(uri).resolve()
            self.assertTrue(target.is_relative_to(ROOT/'contracts'))
            return Resource.from_contents(json.loads(target.read_text(encoding='utf-8')),default_specification=DRAFT202012)
        uri=document.as_uri()+'#/paths/'+path.replace('~','~0').replace('/','~1')+'/'+method+'/responses/'+str(response.status_code)+'/content/application~1json/schema'
        Draft202012Validator({'$ref':uri},registry=Registry(retrieve=retrieve),format_checker=FormatChecker()).validate(response.json())
        self.assertIn('no-store',response['Cache-Control'])

    def test_both_templates_private_independent_neutral_and_source_digest(self):
        self.assertEqual(connection.vendor,'postgresql')
        for template in ['minimal','editorial']:
            response=self.create(template);self.assertEqual(response.status_code,201,response.data)
            self.contract(response,'/api/v1/portfolios/from-template','post')
            item=response.json();self.assertEqual((item['publication_state'],item['visibility'],item['version']),('draft','private',1))
            d=self.design(item);self.contract(d,'/api/v1/portfolios/{id}/design','get');self.assertEqual(d.status_code,200);self.assertEqual(d['ETag'],item['etag'])
            self.assertIn('no-store',d['Cache-Control'])
            model=PortfolioDesign.objects.get(portfolio_id=item['id']);self.assertEqual(model.source_digest,TemplateRegistry().get(template,'1.0.0')['source_digest'])
            hero=next(s for s in d.json()['snapshot']['content']['sections'] if s['type']=='hero')
            self.assertEqual(hero['data']['title'],'Mon portfolio');self.assertNotIn('Camille',str(model.content))

    def test_exact_key_replay_conflict_expiry_and_cleanup(self):
        key=uuid.uuid4();first=self.create(key=key);second=self.create(key=key)
        self.assertEqual(first.json(),second.json());self.assertEqual(Portfolio.objects.count(),1)
        self.assertEqual(self.create(key=key,name='Autre portfolio').status_code,409)
        TemplateCreationRequest.objects.update(expires_at=timezone.now()-timedelta(seconds=1))
        call_command('prune_template_requests',verbosity=0);self.assertEqual(TemplateCreationRequest.objects.count(),1)
        call_command('prune_template_requests',execute=True,verbosity=0);self.assertEqual(TemplateCreationRequest.objects.count(),0)
        third=self.create(key=key);self.assertNotEqual(third.json()['id'],first.json()['id'])

    def test_failure_rolls_back_portfolio_design_and_key(self):
        with patch('modules.templates.instance_services.design_record',side_effect=RuntimeError('synthetic failure')):
            with self.assertRaises(RuntimeError):self.create()
        self.assertFalse(Portfolio.objects.exists());self.assertFalse(PortfolioDesign.objects.exists());self.assertFalse(TemplateCreationRequest.objects.exists())

    def test_save_reload_conflict_and_protected_documents(self):
        item=self.create().json();record=self.design(item).json();snapshot=record['snapshot']
        snapshot['content']['sections'][0]['data']['title']='Un titre personnel'
        snapshot['customization']['section_order']=['hero','skills','about','projects','contact']
        snapshot['customization']['sections']=[{'section_id':'about','visible':False},{'section_id':'projects','presentation':{'spacing':'airy'}}]
        payload={k:snapshot[k] for k in ['content','customization']};path=f"/api/v1/portfolios/{item['id']}/design"
        self.assertEqual(self.send(path,payload,'put').status_code,428)
        saved=self.send(path,payload,'put',tag=record['etag']);self.assertEqual(saved.status_code,200,saved.data)
        self.contract(saved,'/api/v1/portfolios/{id}/design','put')
        self.assertEqual(saved.json()['version'],2)
        self.assertEqual(self.send(path,payload,'put',tag=record['etag']).status_code,412)
        self.assertEqual(self.design(item).json()['snapshot']['content'],payload['content'])
        payload['composition']=snapshot['composition'];self.assertEqual(self.send(path,payload,'put',tag=saved.json()['etag']).status_code,400)

    def test_invalid_unicode_versions_links_visibility_and_duplicate_keys(self):
        self.assertEqual(self.create(template_version='1.٠.0').status_code,400)
        item=self.create().json();record=self.design(item).json();path=f"/api/v1/portfolios/{item['id']}/design"
        for mutation in ['visible','email','link','order','setting']:
            doc=copy.deepcopy(record['snapshot'])
            if mutation=='visible':doc['customization']['sections']=[{'section_id':'hero','visible':False}]
            if mutation=='email':next(s for s in doc['content']['sections'] if s['type']=='contact')['data']['email']='bad-email'
            if mutation=='link':next(s for s in doc['content']['sections'] if s['type']=='projects')['data']['items']=[{'id':str(uuid.uuid4()),'title':'Projet','summary':'','url':'javascript:alert(1)'}]
            if mutation=='order':doc['customization']['section_order']=['contact','hero','about','skills','projects']
            if mutation=='setting':doc['customization']['sections']=[{'section_id':'hero','presentation':{'spacing':'free-css'}}]
            response=self.send(path,{k:doc[k] for k in ['content','customization']},'put',tag=record['etag'])
            self.assertEqual(response.status_code,400,mutation)
        token=self.client.get('/api/v1/auth/csrf').json()['csrf_token']
        response=self.client.put(path,b'{"content":{},"content":{}}',content_type='application/json',HTTP_X_CSRFTOKEN=token,HTTP_IF_MATCH=record['etag'])
        self.assertEqual(response.status_code,400)
        response=self.client.put(path,b' '* (256*1024+1),content_type='application/json',HTTP_X_CSRFTOKEN=token,HTTP_IF_MATCH=record['etag'])
        self.assertEqual(response.status_code,413)
        self.assertEqual(self.design(item).json()['version'],1)
        large=copy.deepcopy(record['snapshot'])
        projects=next(s for s in large['content']['sections'] if s['type']=='projects')
        projects['data']['items']=[{'id':str(uuid.uuid4()),'title':'Projet','summary':'x'*900,'url':None} for _ in range(24)]
        response=self.send(path,{k:large[k] for k in ['content','customization']},'put',tag=record['etag'])
        self.assertEqual(response.status_code,200,response.data)
        response=self.client.post('/api/v1/auth/login',b' '*17000,content_type='application/json',HTTP_X_CSRFTOKEN=token)
        self.assertEqual(response.status_code,400)

    def test_access_csrf_missing_template_and_blank_portfolios(self):
        self.assertEqual(self.create(account_id=str(self.account.pk)).status_code,400)
        self.assertEqual(self.send('/api/v1/portfolios/from-template',{'name':'No key'}).status_code,400)
        item=self.create().json();path=f"/api/v1/portfolios/{item['id']}/design"
        self.assertEqual(self.client.put(path,{},format='json').status_code,403)
        other=get_user_model().objects.create_user(email='other-instance@example.test',password=secrets.token_urlsafe(30))
        self.client.force_authenticate(other)
        self.assertEqual(self.client.get(path).status_code,404)
        self.assertEqual(self.send(path,{},'put',tag='bad').status_code,404)
        self.client.force_authenticate(self.user)
        blank=Portfolio.objects.create(account=self.account,name='Portfolio vierge',slug='blank')
        self.assertEqual(self.client.get(f'/api/v1/portfolios/{blank.pk}/design').status_code,409)
        self.assertEqual(self.create(template='unknown').status_code,404)
        self.client.force_authenticate(None)
        self.client.logout();self.assertEqual(self.client.get(path).status_code,401)

    def test_catalogue_retirement_does_not_break_saved_instances_or_replay(self):
        key=uuid.uuid4();item=self.create(key=key).json()
        with patch('modules.templates.instance_services.TemplateRegistry',side_effect=RegistryInvalid('offline')):
            self.assertEqual(self.create(key=key).json(),item)
            self.assertEqual(self.design(item).status_code,200)
            self.assertEqual(self.create().status_code,503)

    def test_duplicate_resources_independent_archive_restore_delete_and_replay(self):
        key=uuid.uuid4();item=self.create(key=key).json();doc=self.design(item).json()
        next(s for s in doc['snapshot']['content']['sections'] if s['type']=='projects')['data']['items']=[{'id':str(uuid.uuid4()),'title':'Étude locale','summary':'Résumé','url':None}]
        saved=self.send(f"/api/v1/portfolios/{item['id']}/design",{k:doc['snapshot'][k] for k in ['content','customization']},'put',tag=item['etag']).json()
        copy_result=self.send(f"/api/v1/portfolios/{item['id']}/duplicate",{},tag=saved['etag'])
        self.assertEqual(copy_result.status_code,201,copy_result.data);duplicate=copy_result.json()
        a=PortfolioDesign.objects.get(portfolio_id=item['id']);b=PortfolioDesign.objects.get(portfolio_id=duplicate['id'])
        self.assertNotEqual(a.pk,b.pk);self.assertEqual(a.source_digest,b.source_digest)
        a_project=next(s for s in a.content['sections'] if s['type']=='projects')['data']['items'][0]
        b_project=next(s for s in b.content['sections'] if s['type']=='projects')['data']['items'][0]
        self.assertNotEqual(a_project['id'],b_project['id'])
        b.content['sections'][0]['data']['title']='Copie';b.save();a.refresh_from_db();self.assertNotEqual(a.content,b.content)
        archived=self.send(f"/api/v1/portfolios/{item['id']}/archive",{},tag=saved['etag']).json()
        self.assertEqual(self.send(f"/api/v1/portfolios/{item['id']}/design",{k:doc['snapshot'][k] for k in ['content','customization']},'put',tag=archived['etag']).status_code,409)
        restored=self.send(f"/api/v1/portfolios/{item['id']}/restore",{},tag=archived['etag']).json()
        self.assertEqual(self.send(f"/api/v1/portfolios/{item['id']}",{'confirm':True},'delete',tag=restored['etag']).status_code,204)
        self.assertEqual(self.create(key=key).status_code,404)

class InstanceConcurrencyTests(TransactionTestCase):
    def setUp(self):
        self.user=get_user_model().objects.create_user(email='parallel-design@example.test',password=secrets.token_urlsafe(30))
        ensure_personal_account(self.user)

    def parallel(self,operation):
        from concurrent.futures import ThreadPoolExecutor
        from threading import Barrier
        from django.db import connections
        barrier=Barrier(2)
        def worker(index):
            try:barrier.wait(timeout=10);return operation(index)
            finally:connections.close_all()
        with ThreadPoolExecutor(max_workers=2) as pool:return list(pool.map(worker,[0,1]))

    def create(self,key):
        client=APIClient();client.force_authenticate(self.user)
        return client.post('/api/v1/portfolios/from-template',{'name':'Concurrent design','template_id':'minimal','template_version':'1.0.0'},format='json',HTTP_IDEMPOTENCY_KEY=str(key))

    def test_parallel_same_key_creates_one_design(self):
        key=uuid.uuid4();responses=self.parallel(lambda _:self.create(key))
        self.assertEqual([r.status_code for r in responses],[201,201])
        self.assertEqual(responses[0].data,responses[1].data)
        self.assertEqual((Portfolio.objects.count(),PortfolioDesign.objects.count(),TemplateCreationRequest.objects.count()),(1,1,1))

    def test_parallel_save_and_portfolio_patch_share_version(self):
        item=self.create(uuid.uuid4()).data;client=APIClient();client.force_authenticate(self.user)
        record=client.get(f"/api/v1/portfolios/{item['id']}/design").data
        def operation(index):
            c=APIClient();c.force_authenticate(self.user)
            if index==0:return c.put(f"/api/v1/portfolios/{item['id']}/design",{k:record['snapshot'][k] for k in ['content','customization']},format='json',HTTP_IF_MATCH=item['etag']).status_code
            return c.patch(f"/api/v1/portfolios/{item['id']}",{'description':'Concurrent metadata'},format='json',HTTP_IF_MATCH=item['etag']).status_code
        self.assertCountEqual(self.parallel(operation),[200,412])
        self.assertEqual(Portfolio.objects.get(pk=item['id']).version,2)

class DesignMigrationTests(TransactionTestCase):
    def setUp(self):
        from django.db.migrations.executor import MigrationExecutor
        self.assertTrue(connection.settings_dict['NAME'].startswith('test_'))
        self.latest=MigrationExecutor(connection).loader.graph.leaf_nodes()
        MigrationExecutor(connection).migrate([('templates',None)])
        self.apps=MigrationExecutor(connection).loader.project_state([('portfolios','0004_contract_legacy_owner')]).apps

    def tearDown(self):
        from django.db.migrations.executor import MigrationExecutor
        self.apps.get_model('portfolios','Portfolio').objects.update(source_template_id=None,source_template_version=None)
        MigrationExecutor(connection).migrate(self.latest)
        super().tearDown()

    def sample(self):
        user=self.apps.get_model('identity','User').objects.create(email='design-migration@example.test',password='!synthetic-unusable')
        account=self.apps.get_model('accounts','Account').objects.create(owner_id=user.pk)
        return self.apps.get_model('portfolios','Portfolio').objects.create(account_id=account.pk,name='Existing blank',slug='existing-blank',version=7,management_state='archived')

    def test_additive_preserves_uuid_dates_and_blank_without_backfill(self):
        from django.db.migrations.executor import MigrationExecutor
        item=self.sample();before=(item.pk,item.version,item.created_at,item.management_state)
        MigrationExecutor(connection).migrate(self.latest)
        current=Portfolio.objects.get(pk=item.pk)
        self.assertEqual((current.pk,current.version,current.created_at,current.management_state),before)
        self.assertFalse(PortfolioDesign.objects.exists())

    def test_inconsistent_source_blocks_migration_without_repair(self):
        from django.db.migrations.executor import MigrationExecutor
        item=self.sample();item.source_template_id='minimal';item.source_template_version='1.0.0';item.save()
        with self.assertRaisesRegex(RuntimeError,'no design'):MigrationExecutor(connection).migrate(self.latest)
        item.refresh_from_db();self.assertEqual(item.source_template_id,'minimal')
