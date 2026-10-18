import secrets
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from django.contrib.auth import get_user_model
from django.db import IntegrityError,connections
from django.test import TransactionTestCase
from rest_framework.test import APIClient
from modules.accounts.models import Account
from modules.accounts.services import ensure_personal_account
from modules.portfolios.models import Portfolio
from modules.portfolios.services import etag

class PortfolioConcurrencyTests(TransactionTestCase):
    def setUp(self):
        self.user=get_user_model().objects.create_user(email='parallel@example.test',password=secrets.token_urlsafe(24),first_name='Concurrent',last_name='Synthetic')

    def run_parallel(self,operation):
        barrier=Barrier(2)
        def worker(index):
            try:
                barrier.wait(timeout=10)
                return operation(index)
            finally:connections.close_all()
        with ThreadPoolExecutor(max_workers=2) as pool:
            return list(pool.map(worker,[0,1]))

    def test_personal_provisioning_parallel_is_idempotent(self):
        ids=self.run_parallel(lambda _:str(ensure_personal_account(self.user).pk))
        self.assertEqual(ids[0],ids[1]);self.assertEqual(Account.objects.filter(owner=self.user).count(),1)

    def test_database_slug_collision_between_connections(self):
        account=ensure_personal_account(self.user)
        def insert(_):
            try:
                Portfolio.objects.create(account_id=account.pk,name='Concurrent portfolio',slug='same-slug')
                return 'created'
            except IntegrityError:return 'conflict'
        self.assertCountEqual(self.run_parallel(insert),['created','conflict'])
        self.assertEqual(Portfolio.objects.count(),1)

    def test_api_collision_returns_clean_conflict(self):
        ensure_personal_account(self.user)
        def create(_):
            client=APIClient();client.force_authenticate(self.user)
            return client.post('/api/v1/portfolios',{'name':'Concurrent portfolio','slug':'same-slug'},format='json').status_code
        self.assertCountEqual(self.run_parallel(create),[201,409])

    def test_stale_parallel_mutation_does_not_overwrite(self):
        item=Portfolio.objects.create(account=ensure_personal_account(self.user),name='Versioned portfolio',slug='versioned')
        original=etag(item)
        def update(index):
            client=APIClient();client.force_authenticate(self.user)
            return client.patch('/api/v1/portfolios/'+str(item.pk),{'description':'Synthetic '+str(index)},format='json',HTTP_IF_MATCH=original).status_code
        self.assertCountEqual(self.run_parallel(update),[200,412])
        item.refresh_from_db();self.assertEqual(item.version,2)
