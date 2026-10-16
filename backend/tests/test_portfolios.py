"""PORT-001: PostgreSQL-isolated, synthetic-user tests."""
import secrets
from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient
from modules.portfolios.models import Portfolio

class PortfolioTests(TestCase):
    def setUp(self):
        User=get_user_model()
        self.a=User.objects.create_user(email="owner@example.test",password=secrets.token_urlsafe(24),first_name="Owner",last_name="Test")
        self.b=User.objects.create_user(email="other@example.test",password=secrets.token_urlsafe(24),first_name="Other",last_name="Test")
        self.client=APIClient();self.client.force_authenticate(self.a)
        self.url="/api/v1/portfolios/"

    def create(self, **extra):
        return self.client.post(self.url,{"name":"Mon portfolio","portfolio_type":"personal",**extra},format="json")

    def test_create_and_owner_is_server_assigned(self):
        r=self.create();self.assertEqual(r.status_code,201)
        p=Portfolio.objects.get();self.assertEqual(p.owner,self.a)
        self.assertEqual(p.status,"draft");self.assertEqual(p.visibility,"private")
        self.assertEqual(p.slug,"mon-portfolio")

    def test_no_mass_assignment(self):
        self.assertEqual(self.create(owner=str(self.b.pk)).status_code,400)
        self.assertEqual(self.create(status="published").status_code,400)
        self.assertEqual(self.create(visibility="public").status_code,400)

    def test_slug_conflicts(self):
        self.assertEqual(self.create().status_code,201)
        self.assertEqual(self.create().status_code,400)

    def test_owner_scoping(self):
        p=self.create().json();key=p["id"]
        self.client.force_authenticate(self.b)
        self.assertEqual(self.client.get(self.url).json()["count"],0)
        self.assertEqual(self.client.get(self.url+key+"/").status_code,404)
        self.assertEqual(self.client.patch(self.url+key+"/",{"name":"Pirate"},format="json").status_code,404)
        self.assertEqual(self.client.delete(self.url+key+"/").status_code,404)
        self.assertEqual(self.client.post(self.url+key+"/duplicate/").status_code,404)

    def test_update_duplicate_soft_delete(self):
        p=self.create().json();url=self.url+p["id"]+"/"
        self.assertEqual(self.client.patch(url,{"description":"Présentation"},format="json").status_code,200)
        dup=self.client.post(url+"duplicate/");self.assertEqual(dup.status_code,201)
        self.assertNotEqual(dup.json()["id"],p["id"])
        self.assertEqual(dup.json()["status"],"draft")
        self.assertEqual(self.client.delete(url).status_code,204)
        self.assertEqual(self.client.get(url).status_code,404)
        self.assertEqual(self.client.get(self.url).json()["count"],1)

    def test_anonymous_is_rejected(self):
        self.client.force_authenticate(user=None)
        self.assertIn(self.client.get(self.url).status_code,(401,403))
        self.assertIn(self.create().status_code,(401,403))
