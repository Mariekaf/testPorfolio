"""Synthetic data in the PostgreSQL test DB only; session and CSRF are real."""
import json,secrets
from unittest.mock import patch
from pathlib import Path
from django.contrib.auth import get_user_model
from django.db import IntegrityError,transaction
from django.test import TestCase
from jsonschema import Draft202012Validator
from rest_framework.test import APIClient
from modules.accounts.models import Account,AccountMembership
from modules.accounts.services import ensure_personal_account,AccountInconsistent
from modules.portfolios.models import Portfolio
from modules.portfolios.references import default_theme
from modules.portfolios.services import etag

class PortfolioTests(TestCase):
    def setUp(self):
        self.password=secrets.token_urlsafe(24)
        self.a=get_user_model().objects.create_user(email='owner@example.test',password=self.password,first_name='Owner',last_name='Synthetic')
        self.b=get_user_model().objects.create_user(email='other@example.test',password=secrets.token_urlsafe(24),first_name='Other',last_name='Synthetic')
        self.account=ensure_personal_account(self.a);self.other=ensure_personal_account(self.b)
        self.client=APIClient(enforce_csrf_checks=True)
        self.post('/api/v1/auth/login',{'email':self.a.email,'password':self.password})
        self.url='/api/v1/portfolios'

    def post(self,url,data,method='post',tag=None,client=None):
        client=client or self.client
        token=client.get('/api/v1/auth/csrf').json()['csrf_token']
        headers={'HTTP_X_CSRFTOKEN':token}
        if tag is not None:headers['HTTP_IF_MATCH']=tag
        return getattr(client,method)(url,data,format='json',**headers)

    def create(self,**extra):
        r=self.post(self.url,{'name':'Mon portfolio',**extra});self.assertEqual(r.status_code,201,r.content)
        return r.json()

    def detail(self,item):return self.url+'/'+item['id']

    def test_multiple_portfolios_default_states_and_contract(self):
        first=self.create();second=self.create()
        self.assertNotEqual(first['id'],second['id']);self.assertNotEqual(first['slug'],second['slug'])
        self.assertEqual(first['account_id'],str(self.account.pk))
        for item in [first,second]:
            self.assertEqual((item['management_state'],item['publication_state'],item['visibility']),('active','draft','private'))
            self.assertEqual(item['initial_theme_id'],default_theme()['id']);self.assertIsNone(item['source_template_id'])
        root=Path(__file__).resolve().parents[2]
        spec=json.loads((root/'contracts/api/portfolios.v1.json').read_text())
        Draft202012Validator(spec['components']['schemas']['Portfolio']).validate(first)
        self.assertEqual(self.client.get(self.url).json()['count'],2)

    def test_same_slug_allowed_across_accounts_but_reserved_after_delete(self):
        item=self.create(slug='identical')
        Portfolio.objects.create(account=self.other,name='Other portfolio',slug='identical')
        conflict=self.post(self.url,{'name':'Collision','slug':'identical'})
        self.assertEqual(conflict.status_code,409)
        self.assertEqual(self.post(self.detail(item),{'confirm':True},'delete',item['etag']).status_code,204)
        self.assertEqual(self.post(self.url,{'name':'Reserved','slug':'identical'}).status_code,409)
        self.assertEqual(self.client.get(self.url).json()['count'],0)
        self.assertEqual(self.client.get(self.detail(item)).status_code,404)

    def test_strict_inputs_and_reference_mass_assignment(self):
        for changes in [{'name':'ab'},{'name':'bad\nname'},{'name':''},{'slug':'bad_slug'},{'description':'x'*501},
                        {'account_id':str(self.other.pk)},{'owner':str(self.b.pk)},{'status':'published'},
                        {'publication_state':'published'},{'visibility':'public'},{'source_template_id':'fake'},
                        {'initial_theme_id':'fake'},{'version':90},{'management_state':'archived'}]:
            with self.subTest(changes=list(changes)):
                self.assertEqual(self.post(self.url,{'name':'Valid name',**changes}).status_code,400)
        item=self.create(name='東京の作品');self.assertTrue(item['slug'].startswith('portfolio'))
        self.assertEqual(self.create(name='My__Name')['slug'],'my-name')

    def test_update_version_and_uuid_unchanged(self):
        item=self.create();url=self.detail(item)
        self.assertEqual(self.post(url,{'name':'Changed'},'patch').status_code,428)
        self.assertEqual(self.post(url,{'name':'Changed'},'patch','*').status_code,412)
        changed=self.post(url,{'name':'Changed','slug':'NEW-SLUG'},'patch',item['etag'])
        self.assertEqual(changed.status_code,200);value=changed.json()
        self.assertEqual(value['id'],item['id']);self.assertEqual(value['slug'],'new-slug');self.assertEqual(value['version'],2)
        self.assertEqual(changed.headers['ETag'],value['etag'])
        self.assertEqual(self.post(url,{'description':'Lost write'},'patch',item['etag']).status_code,412)
        self.assertEqual(self.client.get(url).json()['description'],'')

    def test_archive_read_restore_and_no_normal_mutations(self):
        item=self.create();url=self.detail(item)
        archived=self.post(url+'/archive',{},tag=item['etag']).json()
        self.assertEqual(archived['management_state'],'archived')
        self.assertEqual(self.client.get(self.url).json()['count'],0)
        self.assertEqual(self.client.get(self.url+'?state=archived').json()['count'],1)
        self.assertEqual(self.client.get(url).status_code,200)
        self.assertEqual(self.post(url,{'name':'No change'},'patch',archived['etag']).status_code,409)
        self.assertEqual(self.post(url+'/duplicate',{},tag=archived['etag']).status_code,409)
        self.assertEqual(self.post(url+'/archive',{},tag=archived['etag']).status_code,409)
        restored=self.post(url+'/restore',{},tag=archived['etag']).json()
        self.assertEqual((restored['management_state'],restored['publication_state']),('active','draft'))
        self.assertEqual(restored['version'],3)

    def test_duplication_no_public_fields_no_source_mutation(self):
        item=self.create(description='Synthetic content');url=self.detail(item)
        duplicated=self.post(url+'/duplicate',{},tag=item['etag'])
        self.assertEqual(duplicated.status_code,201)
        result=duplicated.json()
        for key in ['id','slug']:self.assertNotEqual(result[key],item[key])
        self.assertEqual(result['description'],item['description']);self.assertEqual(result['version'],1)
        self.assertEqual(result['publication_state'],'draft');self.assertEqual(result['account_id'],item['account_id'])
        self.assertEqual(self.client.get(url).json(),item)

    def test_delete_confirmation_required_and_hidden_everywhere(self):
        item=self.create();url=self.detail(item)
        for payload in [{},{'confirm':False},{'confirm':'true'},{'confirm':True,'other':1}]:
            self.assertEqual(self.post(url,payload,'delete',item['etag']).status_code,400)
        self.assertEqual(self.post(url,{'confirm':True},'delete',item['etag']).status_code,204)
        self.assertIsNotNone(Portfolio.objects.get(pk=item['id']).deleted_at)
        for action in ['duplicate','archive','restore']:
            self.assertEqual(self.post(url+'/'+action,{},tag=item['etag']).status_code,404)
        self.assertEqual(self.post(url,{'name':'Hidden'},'patch',item['etag']).status_code,404)

    def test_foreign_reads_and_all_mutations_not_found(self):
        foreign=Portfolio.objects.create(account=self.other,name='Other portfolio',slug='other')
        url=self.url+'/'+str(foreign.pk)
        self.assertEqual(self.client.get(self.url).json()['count'],0)
        self.assertEqual(self.client.get(url).status_code,404)
        for action in ['duplicate','archive','restore']:
            self.assertEqual(self.post(url+'/'+action,{},tag=etag(foreign)).status_code,404)
        self.assertEqual(self.post(url,{'name':'No write'},'patch',etag(foreign)).status_code,404)
        self.assertEqual(self.post(url,{'confirm':True},'delete',etag(foreign)).status_code,404)
        # A forged membership cannot override the canonical owner.
        AccountMembership.objects.create(account=self.other,user=self.a,role='admin')
        self.assertEqual(self.client.get(url).status_code,404)
        self.assertEqual(self.client.get(self.url).json()['count'],0)

    def test_anonymous_csrf_and_canonical_paths(self):
        anon=APIClient(enforce_csrf_checks=True)
        self.assertEqual(anon.get(self.url).status_code,401)
        self.assertEqual(anon.post(self.url,{},format='json').status_code,401)
        self.assertEqual(self.client.post(self.url,{'name':'No csrf'},format='json').status_code,403)
        self.assertEqual(self.client.get(self.url+'/').status_code,404)
        token=self.client.get('/api/v1/auth/csrf').json()['csrf_token']
        self.assertEqual(self.client.post(self.url,{'name':'Forged origin'},format='json',HTTP_X_CSRFTOKEN=token,HTTP_ORIGIN='https://evil.example').status_code,403)

    def test_pagination_and_filters(self):
        Portfolio.objects.bulk_create([Portfolio(account=self.account,name='Synthetic portfolio '+str(i),slug='item-'+str(i)) for i in range(13)])
        first=self.client.get(self.url).json();second=self.client.get(self.url+'?page=2').json()
        self.assertEqual((first['count'],len(first['results']),len(second['results'])),(13,12,1))
        for query in ['?page=0','?page=bad','?state=deleted','?owner=other']:
            self.assertEqual(self.client.get(self.url+query).status_code,400)

    def test_database_constraints_forbidden_publication_and_references(self):
        for changes in [{'status':'published'},{'visibility':'public'},{'version':0},
                        {'management_state':'deleted'},{'source_template_id':'fake'},
                        {'initial_theme_version':'9.0.0'},{'source_template_id':'','source_template_version':'bad'}]:
            with self.subTest(change=changes),self.assertRaises(IntegrityError),transaction.atomic():
                Portfolio.objects.create(account=self.account,name='Synthetic constraint',slug='constraint',**changes)

    def test_personal_provisioning_idempotent_and_inconsistencies_not_repaired(self):
        self.assertEqual(ensure_personal_account(self.a).pk,self.account.pk)
        self.assertEqual(Account.objects.filter(owner=self.a,kind='personal').count(),1)
        membership=AccountMembership.objects.get(account=self.account,user=self.a)
        membership.is_active=False;membership.save(update_fields=['is_active'])
        with self.assertRaises(AccountInconsistent):ensure_personal_account(self.a)
        self.assertEqual(self.post(self.url,{'name':'Do not repair'}).status_code,409)
        membership.refresh_from_db();self.assertFalse(membership.is_active)
        self.assertEqual(self.client.get(self.url).json()['count'],0)

    def test_personal_account_and_membership_database_uniqueness(self):
        for callback in [lambda:Account.objects.create(owner=self.a),lambda:AccountMembership.objects.create(account=self.account,user=self.a)]:
            with self.assertRaises(IntegrityError),transaction.atomic():callback()

    def test_registration_atomic_and_session_contract_unchanged(self):
        anon=APIClient(enforce_csrf_checks=True)
        password=secrets.token_urlsafe(24)
        data={'email':'new@example.test','first_name':'New','last_name':'Synthetic','password':password,'password_confirmation':password}
        with patch('modules.identity.views.ensure_personal_account',side_effect=AccountInconsistent):
            self.assertEqual(self.post('/api/v1/auth/register',data,client=anon).status_code,409)
        self.assertFalse(get_user_model().objects.filter(email=data['email']).exists())
        accounts_before=Account.objects.count();members_before=AccountMembership.objects.count()
        # Fail after Account has been inserted: both identity and account must
        # roll back, not merely the membership or a validation-only path.
        with patch('modules.accounts.services.AccountMembership.objects.create',side_effect=IntegrityError()):
            self.assertEqual(self.post('/api/v1/auth/register',data,client=anon).status_code,503)
        self.assertFalse(get_user_model().objects.filter(email=data['email']).exists())
        self.assertEqual(Account.objects.count(),accounts_before)
        self.assertEqual(AccountMembership.objects.count(),members_before)
        self.assertEqual(self.post('/api/v1/auth/register',data,client=anon).status_code,201)
        user=get_user_model().objects.get(email=data['email'])
        self.assertTrue(Account.objects.filter(owner=user,memberships__user=user).exists())
        self.assertEqual(anon.get('/api/v1/auth/me').status_code,401)
        self.assertEqual(set(self.client.get('/api/v1/auth/me').json()),{'user','expires_at'})

    def test_template_and_theme_schema_validation(self):
        from jsonschema import ValidationError as SchemaError
        root=Path(__file__).resolve().parents[2]
        schema=json.loads((root/'contracts/schemas/templates/template.v1.json').read_text())
        validator=Draft202012Validator(schema)
        valid={'schema_version':1,'id':'future','version':'1.0.0','name':'Future','description':'Synthetic descriptor only','category':'minimal','availability':'unavailable','compatible_themes':[{'id':'studio-neutral','version':'1.0.0'}]}
        validator.validate(valid)
        for change in [{'version':'bad'},{'arbitrary_animation_code':'unsafe'},{'compatible_themes':[]}]:
            with self.assertRaises(SchemaError):validator.validate(valid|change)
