"""E0704: real sessions and PostgreSQL, synthetic accounts only."""
import copy
import secrets
import uuid
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch
from django.contrib.auth import get_user_model
from django.db import connection, transaction, close_old_connections, IntegrityError, DatabaseError
from django.test import TestCase, TransactionTestCase
from rest_framework.test import APIClient
from modules.accounts.services import ensure_personal_account
from modules.templates.models import ReadyPortfolioDesign, ReadyDesignRevision
from modules.templates.ready_registry import ReadyRegistry
from modules.portfolios.models import Portfolio

BASE='/api/v1/ready-portfolios'

class ReadyMixin:
    def setUp(self):
        self.password=secrets.token_urlsafe(32)
        self.user=get_user_model().objects.create_user(email='ready@example.test',password=self.password)
        ensure_personal_account(self.user)
        self.client=APIClient(enforce_csrf_checks=True)
        self.send('/api/v1/auth/login',{'email':self.user.email,'password':self.password})

    def send(self,path,data,method='post',tag=None,key=None,client=None):
        client=client or self.client
        token=client.get('/api/v1/auth/csrf').json()['csrf_token']
        headers={'HTTP_X_CSRFTOKEN':token}
        if tag is not None:headers['HTTP_IF_MATCH']=tag
        if key is not None:headers['HTTP_IDEMPOTENCY_KEY']=str(key)
        return getattr(client,method)(path,data,format='json',**headers)

    def create(self,key=None,name='Mon portfolio'):
        result=self.send(BASE,{'name':name},key=key or uuid.uuid4())
        self.assertEqual(result.status_code,201,result.data)
        return result.json()

    def content(self,record):
        return {k:copy.deepcopy(record['snapshot'][k]) for k in ('content','customization')}

class ReadyInstanceTests(ReadyMixin,TestCase):
    def test_openapi_matches_actual_success_and_error_responses(self):
        import json
        from pathlib import Path
        from jsonschema import Draft202012Validator, FormatChecker
        from referencing import Registry, Resource
        from referencing.jsonschema import DRAFT202012
        root=Path(__file__).resolve().parents[2]/'contracts'
        spec=root/'api/ready-instances.v1.json'
        def retrieve(uri):
            path=Path.from_uri(uri).resolve()
            self.assertTrue(path.is_relative_to(root))
            return Resource.from_contents(json.loads(path.read_text(encoding='utf-8')),default_specification=DRAFT202012)
        def check(result,path,method):
            pointer=path.replace('~','~0').replace('/','~1')
            schema={'$ref':spec.as_uri()+f'#/paths/{pointer}/{method}/responses/{result.status_code}/content/application~1json/schema'}
            Draft202012Validator(schema,registry=Registry(retrieve=retrieve),format_checker=FormatChecker()).validate(result.json())
            self.assertIn('no-store',result['Cache-Control'])
        check(self.client.get('/api/v1/ready-templates'),'/api/v1/ready-templates','get')
        created=self.send(BASE,{'name':'Contrat synthétique'},key=uuid.uuid4());check(created,BASE,'post')
        r=created.json();path=BASE+'/'+r['portfolio']['id'];contract=BASE+'/{id}';data=self.content(r)
        check(self.client.get(path),contract,'get')
        check(self.send(path+'/validate',data),contract+'/validate','post')
        check(self.client.get(path+'/revisions'),contract+'/revisions','get')
        check(self.send(path,data,'put'),contract,'put')
        check(self.send(path,data,'put',tag=r['etag']),contract,'put')
        check(self.send(path,data,'put',tag=r['etag']),contract,'put')
        check(self.send(path,{'content':{}},'put',tag=self.client.get(path).json()['etag']),contract,'put')

    def test_private_catalogue_and_neutral_creation_and_resume(self):
        source=ReadyRegistry().get(); result=self.client.get('/api/v1/ready-templates')
        self.assertEqual(result.status_code,200);self.assertEqual(result.json()['status'],'draft')
        record=self.create();item=record['portfolio'];self.assertEqual((item['visibility'],item['publication_state']),('private','draft'))
        self.assertEqual(record['snapshot'],source['bundle']['snapshot'])
        self.assertEqual(len(record['snapshot']['content']['slots']),14)
        read=self.client.get(BASE+'/'+item['id']);self.assertEqual(read.json(),record)
        self.assertIn('no-store',read['Cache-Control'])
        self.assertEqual(ReadyDesignRevision.objects.count(),1)
        self.assertEqual(self.client.get('/api/v1/templates').json()['count'],2)

    def test_save_all_slots_and_styles_complete_document(self):
        import json
        from pathlib import Path
        root=Path(__file__).resolve().parents[2]
        fixture=json.loads((root/'contracts/fixtures/ready-rendering/demonstration.v1.json').read_text(encoding='utf-8'))['cases'][0]['document']
        from tests.media_fixtures import image_upload
        from modules.media.services import import_images
        image=import_images(self.user,[image_upload()])[0]
        fixture=copy.deepcopy(fixture)
        slots=fixture['content']['slots']
        slots['brand_logo']['value']['asset_id']=str(image.pk)
        slots['hero_portrait']['value']['asset_id']=str(image.pk)
        for project in slots['selected_projects']['items']:
            if project['cover']:project['cover']['asset_id']=str(image.pk)
        record=self.create();data={k:fixture[k] for k in ('content','customization')}
        data['customization']['style_overrides']={'palette_id':'paper-cobalt','font_ref':{'id':'system-serif','version':'1.0.0'}}
        result=self.send(BASE+'/'+record['portfolio']['id'],data,'put',tag=record['etag'])
        self.assertEqual(result.status_code,200,result.data);updated=result.json()
        self.assertEqual(updated['version'],2);self.assertNotEqual(updated['etag'],record['etag'])
        self.assertEqual(updated['snapshot']['content'],fixture['content'])
        self.assertEqual(updated['media_status'],'unavailable')
        self.assertEqual(self.client.get(BASE+'/'+record['portfolio']['id']).json(),updated)
        self.assertEqual(ReadyDesignRevision.objects.count(),2)
        self.assertEqual(ReadyRegistry().get()['bundle']['snapshot'],record['snapshot'])

    def test_preconditions_and_conflicts_do_not_erase(self):
        r=self.create();path=BASE+'/'+r['portfolio']['id'];data=self.content(r)
        self.assertEqual(self.send(path,data,'put').status_code,428)
        self.assertEqual(self.send(path,data,'put',tag='*').status_code,412)
        self.assertEqual(self.send(path,data,'put',tag=r['etag']).status_code,200)
        self.assertEqual(self.send(path,data,'put',tag=r['etag']).status_code,412)
        self.assertEqual(ReadyDesignRevision.objects.count(),2)

    def test_idempotency_and_distinct_intents(self):
        key=uuid.uuid4();a=self.create(key);b=self.create(key)
        self.assertEqual(a,b);self.assertEqual(ReadyPortfolioDesign.objects.count(),1)
        self.assertEqual(self.send(BASE,{'name':'Autre nom'},key=key).status_code,409)
        self.create();self.assertEqual(ReadyPortfolioDesign.objects.count(),2)
        self.assertEqual(self.send(BASE,{'name':'Sans clé'}).status_code,400)

    def test_other_account_cannot_read_write_preview_or_revisions(self):
        r=self.create();path=BASE+'/'+r['portfolio']['id']
        other=get_user_model().objects.create_user(email='other-ready@example.test',password=self.password)
        ensure_personal_account(other);client=APIClient(enforce_csrf_checks=True)
        self.send('/api/v1/auth/login',{'email':other.email,'password':self.password},client=client)
        for suffix in ('','/revisions'):
            self.assertEqual(client.get(path+suffix).status_code,404)
        self.assertEqual(self.send(path,self.content(r),'put',tag=r['etag'],client=client).status_code,404)
        self.assertEqual(self.send(path+'/validate',self.content(r),client=client).status_code,404)

    def test_anonymous_and_csrf(self):
        client=APIClient(enforce_csrf_checks=True)
        self.assertEqual(client.get('/api/v1/ready-templates').status_code,401)
        self.assertEqual(client.get(BASE+'/'+str(uuid.uuid4())).status_code,401)
        self.assertEqual(client.post(BASE,{'name':'x'},format='json').status_code,401)
        self.assertEqual(self.client.post(BASE,{'name':'x'},format='json').status_code,403)

    def test_closed_schema_and_invalid_values_preserve_revision(self):
        r=self.create();path=BASE+'/'+r['portfolio']['id']
        mutations=[lambda d:d['content']['slots']['hero_title'].update(value='x'*161),
            lambda d:d['customization']['style_overrides'].update(colors={'text':'#172620'}),
            lambda d:d['content']['slots']['hero_cta'].update(target={'kind':'external','url':'javascript:alert(1)'}),
            lambda d:d['content']['slots'].update(injected={'type':'text','value':'x'}),
            lambda d:d['content']['slots'].pop('identity_name'),
            lambda d:d['customization'].update(css='body{}')]
        for mutate in mutations:
            data=self.content(r);mutate(data)
            self.assertEqual(self.send(path,data,'put',tag=r['etag']).status_code,400)
        self.assertEqual(self.client.get(path).json(),r)
        self.assertEqual(ReadyDesignRevision.objects.count(),1)

    def test_validation_is_non_persistent_and_empty_drafts_valid(self):
        r=self.create();path=BASE+'/'+r['portfolio']['id'];data=self.content(r)
        data['content']['slots']['identity_name']['value']='Création synthétique'
        result=self.send(path+'/validate',data)
        self.assertEqual(result.status_code,200,result.data)
        self.assertEqual(result.json()['version'],1)
        self.assertEqual(self.client.get(path).json(),r)
        self.assertEqual(ReadyDesignRevision.objects.count(),1)

    def test_failure_after_save_rolls_back_both_document_and_version(self):
        r=self.create();data=self.content(r);data['content']['slots']['hero_title']['value']='Nouvelle idée'
        with patch('modules.templates.ready_instances.revision',side_effect=RuntimeError('synthetic interruption')):
            with self.assertRaises(RuntimeError):self.send(BASE+'/'+r['portfolio']['id'],data,'put',tag=r['etag'])
        self.assertEqual(self.client.get(BASE+'/'+r['portfolio']['id']).json(),r)
        self.assertEqual(ReadyDesignRevision.objects.count(),1)

    def test_creation_failure_is_atomic(self):
        with patch('modules.templates.ready_instances.revision',side_effect=RuntimeError('synthetic interruption')):
            with self.assertRaises(RuntimeError):self.send(BASE,{'name':'Brouillon'},key=uuid.uuid4())
        self.assertFalse(Portfolio.objects.exists());self.assertFalse(ReadyPortfolioDesign.objects.exists())

    def test_archived_deleted_and_duplicate_fail_closed(self):
        r=self.create();path=BASE+'/'+r['portfolio']['id']
        dup=self.send('/api/v1/portfolios/'+r['portfolio']['id']+'/duplicate',{},tag=r['etag'])
        self.assertEqual(dup.status_code,409);self.assertEqual(Portfolio.objects.count(),1)
        item=Portfolio.objects.get(pk=r['portfolio']['id']);item.management_state='archived';item.save()
        self.assertEqual(self.send(path,self.content(r),'put',tag=r['etag']).status_code,409)
        from django.utils import timezone
        item.deleted_at=timezone.now();item.save()
        self.assertEqual(self.client.get(path).status_code,404)

    def test_revision_trigger_and_schema_constraint(self):
        self.create();revision=ReadyDesignRevision.objects.first()
        with self.assertRaisesRegex(DatabaseError, "append-only"):
            with transaction.atomic():ReadyDesignRevision.objects.filter(pk=revision.pk).update(version=99)
        with self.assertRaisesRegex(DatabaseError, "append-only"):
            with transaction.atomic():revision.delete()
        with self.assertRaises(IntegrityError):
            with transaction.atomic():ReadyPortfolioDesign.objects.update(document={'schema_version':2})

    def test_provenance_corruption_is_not_silently_repaired(self):
        r=self.create();ReadyPortfolioDesign.objects.update(source_digest='a'*64)
        result=self.client.get(BASE+'/'+r['portfolio']['id']);self.assertEqual(result.status_code,409)
        self.assertEqual(ReadyPortfolioDesign.objects.get().source_digest,'a'*64)

    def test_size_limits_and_no_cross_schema_writes(self):
        r=self.create();path=BASE+'/'+r['portfolio']['id']
        huge={'content':'x'*262145,'customization':{}}
        self.assertEqual(self.send(path,huge,'put',tag=r['etag']).status_code,413)
        data=self.content(r);data['schema_version']=2
        self.assertEqual(self.send(path,data,'put',tag=r['etag']).status_code,400)
        self.assertEqual(self.client.get('/api/v1/portfolios/'+r['portfolio']['id']+'/design').status_code,409)

class ReadyConcurrencyTests(ReadyMixin,TransactionTestCase):
    def test_same_etag_only_one_writer_commits(self):
        from threading import Barrier
        r=self.create();barrier=Barrier(2);cookies=copy.copy(self.client.cookies)
        def save(index):
            close_old_connections()
            try:
                c=APIClient(enforce_csrf_checks=True);c.cookies=copy.copy(cookies)
                token=c.get('/api/v1/auth/csrf').json()['csrf_token']
                data=self.content(r);data['content']['slots']['hero_title']['value']=f'Synthétique {index}'
                barrier.wait(timeout=10)
                result=c.put(BASE+'/'+r['portfolio']['id'],data,format='json',HTTP_X_CSRFTOKEN=token,HTTP_IF_MATCH=r['etag'])
                return result.status_code
            finally:close_old_connections()
        with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(save,[1,2]))
        self.assertEqual(sorted(results),[200,412]);self.assertEqual(ReadyDesignRevision.objects.count(),2)

class ReadyMigrationTests(ReadyMixin,TransactionTestCase):
    def test_additive_migration_preserves_v1_v2_and_sessions(self):
        from django.db.migrations.executor import MigrationExecutor
        from django.test import override_settings
        from modules.templates.models import PortfolioDesign, DesignTransition
        from modules.templates.validation import snapshot_of
        old=('templates','0002_versioned_design_transitions')
        new=('templates','0003_readyportfoliodesign_readydesignrevision_and_more')
        executor=MigrationExecutor(connection);executor.migrate([old])
        try:
            items=[]
            for template in ('minimal','editorial'):
                r=self.send('/api/v1/portfolios/from-template',{'name':'Ancien synthétique','template_id':template,'template_version':'1.0.0'},key=uuid.uuid4())
                self.assertEqual(r.status_code,201,r.data);items.append(r.json())
            with override_settings(SAAS_HERO_TRANSITIONS_ENABLED=True):
                upgraded=self.send('/api/v1/portfolios/'+items[1]['id']+'/design/upgrade',{'target_schema_version':2,'converter_version':'1.0.0'},tag=items[1]['etag'],key=uuid.uuid4())
                self.assertEqual(upgraded.status_code,200,upgraded.data)
            documents={str(d.pk):snapshot_of(d) for d in PortfolioDesign.objects.all()}
            transitions=list(DesignTransition.objects.values())
            session=self.client.get('/api/v1/auth/me').json()
            MigrationExecutor(connection).migrate([new])
            self.assertEqual({str(d.pk):snapshot_of(d) for d in PortfolioDesign.objects.all()},documents)
            self.assertEqual(list(DesignTransition.objects.values()),transitions)
            self.assertEqual(self.client.get('/api/v1/auth/me').json(),session)
            self.assertFalse(ReadyPortfolioDesign.objects.exists())
        finally:MigrationExecutor(connection).migrate([new])

    def test_guard_forbids_existing_names_or_missing_authorization(self):
        import importlib,os
        from types import SimpleNamespace
        guard=importlib.import_module('modules.templates.migrations.0003_readyportfoliodesign_readydesignrevision_and_more').isolated_only
        for name,consent in [('portfolio_core_dev','1'),('test_previous','1'),('test_e04_synthetic','0')]:
            with patch.dict(os.environ,{'SAAS_E0704_ISOLATED_MIGRATIONS':consent}):
                with self.assertRaises(RuntimeError):guard(None,SimpleNamespace(connection=SimpleNamespace(settings_dict={'NAME':name})))
