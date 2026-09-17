from datetime import date

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from crm.models import Business, Company, Contact, Deal, Membership, Task


class CRMInteractionTests(TestCase):
    def setUp(self):
        self.business = Business.objects.create(name="UI Business", slug="ui-business")
        self.user = User.objects.create_user(
            username="uiuser",
            password="StrongPass123!",
            email="ui@example.com",
        )
        Membership.objects.create(
            user=self.user,
            business=self.business,
            role=Membership.ADMIN,
        )
        self.company = Company.objects.create(
            business=self.business,
            name="Acme",
            industry="Technology",
            email="hello@acme.test",
        )
        self.contact = Contact.objects.create(
            business=self.business,
            company=self.company,
            first_name="Jane",
            last_name="Doe",
            job_title="Buyer",
        )
        self.deal = Deal.objects.create(
            business=self.business,
            company=self.company,
            contact=self.contact,
            title="Acme Renewal",
            value=5000,
            stage=Deal.NEGOTIATION,
        )
        self.task = Task.objects.create(
            business=self.business,
            company=self.company,
            contact=self.contact,
            deal=self.deal,
            title="Call Jane",
            due_date=date(2026, 9, 20),
        )
        self.client.force_login(self.user)

    def test_task_toggle_changes_completion_state(self):
        response = self.client.post(reverse("crm:task_toggle", args=[self.task.id]))
        self.assertRedirects(response, reverse("crm:task_detail", args=[self.task.id]))
        self.task.refresh_from_db()
        self.assertTrue(self.task.completed)

    def test_header_search_suggestions_are_business_isolated(self):
        other = Business.objects.create(name="Other", slug="other")
        Company.objects.create(business=other, name="Acme Other")
        response = self.client.get(reverse("crm:search_suggestions"), {"q": "Acme"})
        self.assertEqual(response.status_code, 200)
        titles = [item["title"] for item in response.json()["results"]]
        self.assertIn("Acme", titles)
        self.assertNotIn("Acme Other", titles)

    def test_company_search_filters_results(self):
        response = self.client.get(reverse("crm:company_list"), {"q": "Technology"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(response.context["companies"]), [self.company])

    def test_deal_stage_filter_works(self):
        response = self.client.get(
            reverse("crm:deal_list"),
            {"stage": Deal.NEGOTIATION},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(response.context["deals"]), [self.deal])

    def test_task_status_filter_works(self):
        response = self.client.get(
            reverse("crm:task_list"),
            {"status": "completed"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(response.context["tasks"]), [])
