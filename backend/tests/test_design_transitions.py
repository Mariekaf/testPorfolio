"""E04 integration: disposable PostgreSQL only, real locking/transactions/triggers."""
import copy
import secrets
import uuid
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from unittest.mock import patch
from django.contrib.auth import get_user_model
from django.db import connection, connections, transaction, DatabaseError
from django.test import TestCase, TransactionTestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIClient
from modules.accounts.services import ensure_personal_account
from modules.portfolios.models import Portfolio
from modules.templates.models import PortfolioDesign, DesignTransition
from modules.templates.transitions import transition, persist, verify_revision
from modules.portfolios.services import PortfolioProblem

UPGRADE={'target_schema_version':2,'converter_version':'1.0.0'}


class TransitionHelpers:
    def setUp(self):
        self.assertEqual(connection.vendor,'postgresql')
        self.assertTrue(connection.settings_dict['NAME'].startswith('test_e04_'))
        self.user=get_user_model().objects.create_user(email='e04-owner@example.test',password=secrets.token_urlsafe(24))
        self.account=ensure_personal_account(self.user)
        self.client=APIClient();self.client.force_authenticate(self.user)

    def create(self,template='minimal'):
        r=self.client.post('/api/v1/portfolios/from-template',{'name':'Portfolio synthétique E04','template_id':template,'template_version':'1.0.0'},format='json',HTTP_IDEMPOTENCY_KEY=str(uuid.uuid4()))
        self.assertEqual(r.status_code,201,r.data)
        return r.json()

    def send(self,item,action='upgrade',data=None,key=None,tag=None,client=None):
        return (client or self.client).post(f"/api/v1/portfolios/{item['id']}/design/{action}",data if data is not None else UPGRADE,format='json',HTTP_IF_MATCH=tag or item['etag'],HTTP_IDEMPOTENCY_KEY=str(key or uuid.uuid4()))

    def record(self,item,accept='1'):
        return self.client.get(f"/api/v1/portfolios/{item['id']}/design",HTTP_ACCEPT_DESIGN_SCHEMA=accept)


@override_settings(SAAS_HERO_TRANSITIONS_ENABLED=True)
class TransitionTests(TransitionHelpers,TestCase):
    def test_migration_guard_rejects_other_names_and_missing_consent(self):
        import importlib,os
        from types import SimpleNamespace
        guard=importlib.import_module('modules.templates.migrations.0002_versioned_design_transitions').require_isolated_authorization
        for name,authorization in [('portfolio_core_dev','1'),('test_previous_validation','1'),('test_e04_synthetic','0')]:
            editor=SimpleNamespace(connection=SimpleNamespace(settings_dict={'NAME':name}))
            with patch.dict(os.environ,{'SAAS_E04_ISOLATED_MIGRATIONS':authorization}):
                with self.assertRaisesRegex(RuntimeError,'not authorized'):guard(None,editor)

    def test_openapi_actual_success_error_and_recovery_responses(self):
        import json
        from pathlib import Path
        from jsonschema import Draft202012Validator,FormatChecker
        from referencing import Registry,Resource
        from referencing.jsonschema import DRAFT202012
        from modules.templates.registry import ROOT
        spec=ROOT/'contracts/api/hero-design.v2.json'
        def retrieve(uri):
            target=Path.from_uri(uri).resolve()
            self.assertTrue(target.is_relative_to(ROOT/'contracts'))
            return Resource.from_contents(json.loads(target.read_text(encoding='utf-8')),default_specification=DRAFT202012)
        def verify(response,path,method):
            pointer=path.replace('~','~0').replace('/','~1')
            schema={'$ref':spec.as_uri()+f'#/paths/{pointer}/{method}/responses/{response.status_code}/content/application~1json/schema'}
            Draft202012Validator(schema,registry=Registry(retrieve=retrieve),format_checker=FormatChecker()).validate(response.json())
            self.assertIn('no-store',response['Cache-Control'])
        item=self.create();base='/api/v1/portfolios/{id}/design'
        verify(self.record(item),base,'get')
        upgraded=self.send(item);verify(upgraded,base+'/upgrade','post')
        verify(self.record(item),base,'get')
        verify(self.record(item,'2'),base,'get')
        body=upgraded.json();revision=body['recovery_revision_id'];route=f"/api/v1/portfolios/{item['id']}/design/revisions"
        verify(self.client.get(route),base+'/revisions','get')
        verify(self.client.get(route+'/'+revision),base+'/revisions/{revision_id}','get')
        verify(self.send(item),base+'/upgrade','post')
        verify(self.send(item,'restore',{'recovery_revision_id':revision},tag=body['etag']),base+'/restore','post')

    def test_both_templates_full_lifecycle_and_exact_recovery(self):
        for template in ('minimal','editorial'):
            item=self.create(template);before=self.record(item).json()['snapshot']
            design=PortfolioDesign.objects.get(portfolio_id=item['id']);identity=design.pk;digest=design.source_digest
            key=uuid.uuid4();converted=self.send(item,key=key)
            self.assertEqual(converted.status_code,200,converted.data)
            body=converted.json();revision=DesignTransition.objects.get(pk=body['recovery_revision_id'])
            self.assertEqual(revision.before_snapshot,before)
            self.assertEqual((revision.before_version,revision.after_version),(1,2))
            self.assertEqual(self.record(item).status_code,406)
            self.assertEqual(self.record(item,'2').status_code,200)
            current=self.record(item,'1,2').json();payload={k:current['snapshot'][k] for k in ('content','customization')}
            payload['content']['sections'][0]['data']['title']='Édition v2 à récupérer'
            saved=self.client.put(f"/api/v1/portfolios/{item['id']}/design",payload,format='json',HTTP_IF_MATCH=body['etag'],HTTP_ACCEPT_DESIGN_SCHEMA='2')
            self.assertEqual(saved.status_code,200,saved.data)
            replay=self.send(item,key=key);self.assertEqual(replay.json(),body)
            self.assertEqual(self.send(item,tag=saved['ETag']).status_code,409)
            restore_key=uuid.uuid4();values={'recovery_revision_id':str(revision.pk)}
            restored=self.send(item,'restore',values,restore_key,saved['ETag'])
            self.assertEqual(restored.status_code,200,restored.data)
            self.assertEqual(restored.json()['snapshot'],before)
            backup=DesignTransition.objects.get(pk=restored.json()['recovery_revision_id'])
            self.assertEqual(backup.before_snapshot,saved.json()['snapshot'])
            self.assertEqual(backup.restored_from_id,revision.pk)
            self.assertEqual(self.send(item,'restore',values,restore_key,saved['ETag']).json(),restored.json())
            self.assertEqual(self.record(item).json()['snapshot'],before)
            design.refresh_from_db();self.assertEqual((design.pk,design.source_digest),(identity,digest))
            portfolio=Portfolio.objects.get(pk=item['id'])
            self.assertEqual((portfolio.version,portfolio.status,portfolio.visibility,portfolio.account_id),(4,'draft','private',self.account.pk))
            self.assertEqual(self.send(item,'restore',values,tag=restored['ETag']).status_code,409)
            repeated=self.send(item,tag=restored['ETag'])
            self.assertEqual(repeated.status_code,200,repeated.data)
            self.assertEqual(repeated.json()['version'],5)
            self.assertEqual(DesignTransition.objects.filter(design=design).count(),3)
            revision.refresh_from_db();self.assertEqual(revision.before_snapshot,before)

    def test_flag_off_keeps_v1_default_and_disables_mutations(self):
        item=self.create();before=self.record(item).json()
        with override_settings(SAAS_HERO_TRANSITIONS_ENABLED=False):
            self.assertEqual(self.send(item).status_code,404)
            self.assertEqual(self.record(item).json(),before)
        self.assertFalse(DesignTransition.objects.exists())

    def test_etag_idempotency_and_body_errors(self):
        item=self.create();path=f"/api/v1/portfolios/{item['id']}/design/upgrade"
        self.assertEqual(self.client.post(path,UPGRADE,format='json',HTTP_IDEMPOTENCY_KEY=str(uuid.uuid4())).status_code,428)
        self.assertEqual(self.client.post(path,UPGRADE,format='json',HTTP_IF_MATCH=item['etag']).status_code,400)
        self.assertEqual(self.send(item,data={**UPGRADE,'extra':True}).status_code,400)
        self.assertEqual(self.send(item,data={**UPGRADE,'target_schema_version':2.0}).status_code,400)
        self.assertEqual(self.send(item,tag='"stale"').status_code,412)
        key=uuid.uuid4();first=self.send(item,key=key)
        self.assertEqual(self.send(item,key=key,tag=first['ETag']).status_code,409)
        self.assertEqual(self.send(item).status_code,412)
        self.assertEqual(DesignTransition.objects.count(),1)

    def test_foreign_missing_deleted_and_inconsistent_membership_hidden(self):
        item=self.create();converted=self.send(item).json();rid=converted['recovery_revision_id']
        other=get_user_model().objects.create_user(email='e04-other@example.test',password=secrets.token_urlsafe(24));ensure_personal_account(other)
        self.client.force_authenticate(other)
        self.assertEqual(self.send(item,data={}).status_code,404)
        self.assertEqual(self.record(item,'2').status_code,404)
        self.assertEqual(self.client.get(f"/api/v1/portfolios/{item['id']}/design/revisions/{rid}").status_code,404)
        self.client.force_authenticate(self.user)
        membership=self.account.memberships.get();membership.role='viewer';membership.save()
        self.assertEqual(self.record(item,'2').status_code,404)
        membership.refresh_from_db();self.assertEqual(membership.role,'viewer')
        membership.role='admin';membership.save()
        Portfolio.objects.filter(pk=item['id']).update(deleted_at=timezone.now())
        self.assertEqual(self.record(item,'2').status_code,404)
        self.assertEqual(self.send(item).status_code,404)

    def test_archive_and_foreign_revision_refused(self):
        first=self.create();second=self.create();one=self.send(first).json();two=self.send(second).json()
        self.assertEqual(self.send(first,'restore',{'recovery_revision_id':two['recovery_revision_id']},tag=one['etag']).status_code,404)
        Portfolio.objects.filter(pk=first['id']).update(management_state='archived')
        self.assertEqual(self.send(first,'restore',{'recovery_revision_id':one['recovery_revision_id']},tag=one['etag']).status_code,409)
        self.assertEqual(self.record(first,'2').status_code,200)

    def test_interruptions_roll_back_revision_snapshot_and_version(self):
        for fail_after_save in (False,True):
            item=self.create();before=self.record(item).json()
            def interrupted(*args):
                if fail_after_save:persist(*args)
                raise RuntimeError('Synthetic interruption')
            with patch('modules.templates.transitions.persist',side_effect=interrupted):
                with self.assertRaises(RuntimeError):self.send(item)
            self.assertEqual(self.record(item).json(),before)
            self.assertFalse(DesignTransition.objects.filter(design__portfolio_id=item['id']).exists())

    def test_invalid_candidate_never_creates_revision_or_writes(self):
        item=self.create();before=self.record(item).json()
        from modules.templates.hero_conversion import convert_v1_to_v2
        candidate=convert_v1_to_v2(before['snapshot'])
        candidate['customization']['sections']=[{'section_id':'hero','hero':{'schema_version':1,'appearance':{'palette':{'text':'#F5F5F1'}}}}]
        with patch('modules.templates.transitions.convert_v1_to_v2',return_value=candidate):
            self.assertEqual(self.send(item).status_code,400)
        self.assertEqual(self.record(item).json(),before)
        self.assertFalse(DesignTransition.objects.exists())

    def test_trigger_blocks_update_delete_and_revision_verification_detects_corruption(self):
        item=self.create();body=self.send(item).json();row=DesignTransition.objects.get(pk=body['recovery_revision_id'])
        for operation in ('UPDATE','DELETE'):
            with self.assertRaises(DatabaseError):
                with transaction.atomic():
                    with connection.cursor() as cursor:
                        cursor.execute(("UPDATE templates_designtransition SET converter_version='tampered' WHERE id=%s" if operation=='UPDATE' else 'DELETE FROM templates_designtransition WHERE id=%s'),[row.pk])
        row.refresh_from_db();self.assertEqual(row.converter_version,'1.0.0')
        corrupted=copy.deepcopy(row);corrupted.before_snapshot['content']['sections'][0]['data']['title']='tampered'
        with self.assertRaises(PortfolioProblem):verify_revision(corrupted,row.design)

    def test_put_full_validation_negotiation_no_downgrade_and_gate(self):
        item=self.create();body=self.send(item).json();snapshot=body['snapshot'];path=f"/api/v1/portfolios/{item['id']}/design"
        snapshot['customization']['sections']=[{'section_id':'hero','hero':{'schema_version':1,'appearance':{'palette':{'text':'#F5F5F1'}}}}]
        response=self.client.put(path,{k:snapshot[k] for k in ('content','customization')},format='json',HTTP_IF_MATCH=body['etag'],HTTP_ACCEPT_DESIGN_SCHEMA='2')
        self.assertEqual(response.status_code,400)
        self.assertEqual(self.record(item,'2').json()['version'],2)
        old=DesignTransition.objects.get(pk=body['recovery_revision_id']).before_snapshot
        self.assertEqual(self.client.put(path,{k:old[k] for k in ('content','customization')},format='json',HTTP_IF_MATCH=body['etag'],HTTP_ACCEPT_DESIGN_SCHEMA='2').status_code,400)
        with override_settings(SAAS_HERO_TRANSITIONS_ENABLED=False):
            self.assertEqual(self.client.put(path,{k:body['snapshot'][k] for k in ('content','customization')},format='json',HTTP_IF_MATCH=body['etag'],HTTP_ACCEPT_DESIGN_SCHEMA='2').status_code,409)
        self.assertEqual(self.record(item,'future').status_code,400)

    def test_recovery_reads_are_private_bounded_and_account_scoped(self):
        item=self.create();body=self.send(item).json();path=f"/api/v1/portfolios/{item['id']}/design/revisions"
        listing=self.client.get(path);self.assertEqual(listing.status_code,200)
        self.assertEqual(listing.json()['results'][0]['id'],body['recovery_revision_id'])
        detail=self.client.get(path+'/'+body['recovery_revision_id']);self.assertEqual(detail.status_code,200)
        self.assertIn('no-store',detail['Cache-Control'])
        for query in ('?page=0','?page=1&page=2','?other=1','?page=٠'):
            self.assertEqual(self.client.get(path+query).status_code,400)

    def test_v2_duplication_independent_without_copying_recovery_history(self):
        item=self.create();converted=self.send(item).json()
        duplicate=self.client.post(f"/api/v1/portfolios/{item['id']}/duplicate",{},format='json',HTTP_IF_MATCH=converted['etag'])
        self.assertEqual(duplicate.status_code,201,duplicate.data)
        d=PortfolioDesign.objects.get(portfolio_id=duplicate.json()['id'])
        self.assertEqual(d.schema_version,2);self.assertFalse(d.transitions.exists())
        self.assertNotEqual(d.pk,PortfolioDesign.objects.get(portfolio_id=item['id']).pk)
        self.assertEqual(self.client.get(f"/api/v1/portfolios/{duplicate.json()['id']}/design/revisions/{converted['recovery_revision_id']}").status_code,404)

    def test_real_auth_session_and_csrf_unchanged(self):
        item=self.create();password=secrets.token_urlsafe(24);self.user.set_password(password);self.user.save()
        real=APIClient(enforce_csrf_checks=True)
        token=real.get('/api/v1/auth/csrf').json()['csrf_token']
        login=real.post('/api/v1/auth/login',{'email':self.user.email,'password':password},format='json',HTTP_X_CSRFTOKEN=token)
        self.assertEqual(login.status_code,200)
        self.assertEqual(self.send(item,client=real).status_code,403)
        token=real.get('/api/v1/auth/csrf').json()['csrf_token']
        result=real.post(f"/api/v1/portfolios/{item['id']}/design/upgrade",UPGRADE,format='json',HTTP_X_CSRFTOKEN=token,HTTP_IF_MATCH=item['etag'],HTTP_IDEMPOTENCY_KEY=str(uuid.uuid4()))
        self.assertEqual(result.status_code,200,result.data)


@override_settings(SAAS_HERO_TRANSITIONS_ENABLED=True)
class TransitionConcurrencyTests(TransitionHelpers,TransactionTestCase):
    def parallel(self, operations):
        barrier=Barrier(len(operations))
        def run(operation):
            connections.close_all()
            try:
                user=get_user_model().objects.get(pk=self.user.pk);barrier.wait(timeout=10)
                return operation(user)
            finally:connections.close_all()
        with ThreadPoolExecutor(max_workers=len(operations)) as executor:return list(executor.map(run,operations))

    def test_same_key_simultaneous_commits_exactly_once(self):
        item=self.create();key=uuid.uuid4()
        def operation(user):return transition(user,item['id'],'upgrade',UPGRADE,key,item['etag'])
        results=self.parallel([operation,operation])
        self.assertEqual(results[0],results[1]);self.assertEqual(DesignTransition.objects.count(),1)
        self.assertEqual(Portfolio.objects.get(pk=item['id']).version,2)

    def test_different_keys_same_etag_one_conflict(self):
        item=self.create()
        def operation(user):
            try:transition(user,item['id'],'upgrade',UPGRADE,uuid.uuid4(),item['etag']);return 200
            except PortfolioProblem as error:return error.status
        self.assertCountEqual(self.parallel([operation,operation]),[200,412])
        self.assertEqual(DesignTransition.objects.count(),1)

    def test_restore_same_key_once(self):
        item=self.create();converted=self.send(item).json();key=uuid.uuid4();values={'recovery_revision_id':converted['recovery_revision_id']}
        def operation(user):return transition(user,item['id'],'restore',values,key,converted['etag'])
        results=self.parallel([operation,operation]);self.assertEqual(results[0],results[1])
        self.assertEqual(DesignTransition.objects.count(),2);self.assertEqual(Portfolio.objects.get(pk=item['id']).version,3)

    def test_upgrade_and_legacy_put_share_same_version_lock(self):
        item=self.create();record=self.record(item).json();path=f"/api/v1/portfolios/{item['id']}/design"
        payload={key:record['snapshot'][key] for key in ('content','customization')}
        def upgrade(user):
            try:transition(user,item['id'],'upgrade',UPGRADE,uuid.uuid4(),item['etag']);return 200
            except PortfolioProblem as error:return error.status
        def edit(user):
            client=APIClient();client.force_authenticate(user)
            return client.put(path,payload,format='json',HTTP_IF_MATCH=item['etag']).status_code
        self.assertCountEqual(self.parallel([upgrade,edit]),[200,412])
        self.assertEqual(Portfolio.objects.get(pk=item['id']).version,2)

    def test_lock_timeout_is_retryable_without_partial_write(self):
        item=self.create();key=uuid.uuid4()
        def request():
            connections.close_all()
            try:
                client=APIClient();client.force_authenticate(get_user_model().objects.get(pk=self.user.pk))
                return client.post(f"/api/v1/portfolios/{item['id']}/design/upgrade",UPGRADE,format='json',HTTP_IF_MATCH=item['etag'],HTTP_IDEMPOTENCY_KEY=str(key))
            finally:connections.close_all()
        with ThreadPoolExecutor(max_workers=1) as executor:
            with transaction.atomic():
                Portfolio.objects.select_for_update().get(pk=item['id'])
                response=executor.submit(request).result(timeout=10)
                self.assertEqual(response.status_code,503)
                self.assertEqual(response['Retry-After'],'2')
                self.assertFalse(DesignTransition.objects.exists())
        self.assertEqual(self.send(item,key=key).status_code,200)

class TransitionMigrationTests(TransactionTestCase):
    def test_additive_migration_preserves_v1_without_backfill(self):
        from django.db.migrations.executor import MigrationExecutor
        self.assertTrue(connection.settings_dict['NAME'].startswith('test_e04_'))
        latest=MigrationExecutor(connection).loader.graph.leaf_nodes()
        MigrationExecutor(connection).migrate([('templates','0001_initial')])
        try:
            user=get_user_model().objects.create_user(email='e04-migration@example.test',password=secrets.token_urlsafe(24))
            account=ensure_personal_account(user)
            from modules.templates.registry import TemplateRegistry
            entry=TemplateRegistry().get('minimal','1.0.0');snapshot=entry['snapshot']
            portfolio=Portfolio.objects.create(account=account,name='Migration synthétique',slug='migration-e04',source_template_id='minimal',source_template_version='1.0.0',version=9,management_state='archived')
            design=PortfolioDesign.objects.create(portfolio=portfolio,source_digest=entry['source_digest'],**{key:snapshot[key] for key in ('schema_version','composition','content','presentation','customization','experience')})
            before=(design.pk,design.created_at,design.source_digest,copy.deepcopy(snapshot))
            MigrationExecutor(connection).migrate(latest)
            design.refresh_from_db();portfolio.refresh_from_db()
            from modules.templates.validation import snapshot_of
            self.assertEqual((design.pk,design.created_at,design.source_digest,snapshot_of(design)),before)
            self.assertEqual((portfolio.version,portfolio.management_state),(9,'archived'))
            self.assertFalse(DesignTransition.objects.exists())
        finally:
            MigrationExecutor(connection).migrate(latest)

    @override_settings(SAAS_HERO_TRANSITIONS_ENABLED=True)
    def test_reverse_refused_once_recovery_exists(self):
        helper=TransitionHelpers();helper.assertEqual=self.assertEqual;helper.assertTrue=self.assertTrue
        helper.setUp();item=helper.create();result=helper.send(item)
        self.assertEqual(result.status_code,200)
        from django.db.migrations.executor import MigrationExecutor
        with self.assertRaisesRegex(RuntimeError,'Do not reverse'):
            MigrationExecutor(connection).migrate([('templates','0001_initial')])
        self.assertEqual(DesignTransition.objects.count(),1)
        self.assertEqual(PortfolioDesign.objects.get(portfolio_id=item['id']).schema_version,2)
