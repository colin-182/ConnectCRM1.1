from datetime import date, time

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from crm.models import Business, Company, Contact, Deal, Membership, Task


class CRMCrudTests(TestCase):
    def setUp(self):
        self.business = Business.objects.create(
            name="CRM Business",
            slug="crm-business",
        )
        self.user = User.objects.create_user(
            username="crmuser",
            password="TestPass123!",
            email="crmuser@example.com",
        )
        Membership.objects.create(
            user=self.user,
            business=self.business,
            role=Membership.ADMIN,
        )
        self.client.force_login(self.user)

    def test_company_create_edit_delete(self):
        response = self.client.post(
            reverse("crm:company_create"),
            {
                "name": "Acme",
                "industry": "Technology",
                "phone": "123",
                "email": "hello@acme.test",
                "website": "https://acme.test",
            },
        )
        self.assertRedirects(response, reverse("crm:company_list"))

        company = Company.objects.get(name="Acme")
        self.assertEqual(company.business, self.business)

        response = self.client.post(
            reverse("crm:company_edit", args=[company.id]),
            {
                "name": "Acme Updated",
                "industry": "SaaS",
                "phone": "456",
                "email": "updated@acme.test",
                "website": "https://acme.test",
            },
        )
        self.assertRedirects(
            response,
            reverse("crm:company_detail", args=[company.id]),
        )
        company.refresh_from_db()
        self.assertEqual(company.name, "Acme Updated")

        response = self.client.post(
            reverse("crm:company_delete", args=[company.id])
        )
        self.assertRedirects(response, reverse("crm:company_list"))
        self.assertFalse(Company.objects.filter(id=company.id).exists())

    def test_contact_create_edit_delete(self):
        company = Company.objects.create(
            business=self.business,
            name="Acme",
        )

        response = self.client.post(
            reverse("crm:contact_create"),
            {
                "company": company.id,
                "first_name": "Jane",
                "last_name": "Doe",
                "job_title": "Sales",
                "email": "jane@example.com",
                "phone": "123",
            },
        )
        self.assertRedirects(response, reverse("crm:contact_list"))

        contact = Contact.objects.get(first_name="Jane")
        response = self.client.post(
            reverse("crm:contact_edit", args=[contact.id]),
            {
                "company": company.id,
                "first_name": "Janet",
                "last_name": "Doe",
                "job_title": "Account Manager",
                "email": "janet@example.com",
                "phone": "456",
            },
        )
        self.assertRedirects(
            response,
            reverse("crm:contact_detail", args=[contact.id]),
        )
        contact.refresh_from_db()
        self.assertEqual(contact.first_name, "Janet")

        response = self.client.post(
            reverse("crm:contact_delete", args=[contact.id])
        )
        self.assertRedirects(response, reverse("crm:contact_list"))
        self.assertFalse(Contact.objects.filter(id=contact.id).exists())

    def test_deal_create_edit_delete(self):
        company = Company.objects.create(
            business=self.business,
            name="Acme",
        )
        contact = Contact.objects.create(
            business=self.business,
            company=company,
            first_name="Jane",
            last_name="Doe",
        )

        response = self.client.post(
            reverse("crm:deal_create"),
            {
                "company": company.id,
                "contact": contact.id,
                "title": "New Deal",
                "value": "5000.00",
                "stage": Deal.LEAD,
            },
        )
        self.assertRedirects(response, reverse("crm:deal_list"))

        deal = Deal.objects.get(title="New Deal")
        response = self.client.post(
            reverse("crm:deal_edit", args=[deal.id]),
            {
                "company": company.id,
                "contact": contact.id,
                "title": "Updated Deal",
                "value": "7500.00",
                "stage": Deal.PROPOSAL,
            },
        )
        self.assertRedirects(
            response,
            reverse("crm:deal_detail", args=[deal.id]),
        )
        deal.refresh_from_db()
        self.assertEqual(deal.title, "Updated Deal")
        self.assertEqual(deal.stage, Deal.PROPOSAL)

        response = self.client.post(
            reverse("crm:deal_delete", args=[deal.id])
        )
        self.assertRedirects(response, reverse("crm:deal_list"))
        self.assertFalse(Deal.objects.filter(id=deal.id).exists())

    def test_task_create_edit_delete(self):
        company = Company.objects.create(
            business=self.business,
            name="Acme",
        )
        contact = Contact.objects.create(
            business=self.business,
            company=company,
            first_name="Jane",
            last_name="Doe",
        )
        deal = Deal.objects.create(
            business=self.business,
            company=company,
            contact=contact,
            title="Deal",
            value=1000,
        )

        response = self.client.post(
            reverse("crm:task_create"),
            {
                "company": company.id,
                "contact": contact.id,
                "deal": deal.id,
                "title": "Call Jane",
                "description": "Follow up",
                "due_date": "2026-09-20",
                "due_time": "10:00",
                "completed": "",
            },
        )
        self.assertRedirects(response, reverse("crm:task_list"))

        task = Task.objects.get(title="Call Jane")
        self.assertEqual(task.due_date, date(2026, 9, 20))
        self.assertEqual(task.due_time, time(10, 0))

        response = self.client.post(
            reverse("crm:task_edit", args=[task.id]),
            {
                "company": company.id,
                "contact": contact.id,
                "deal": deal.id,
                "title": "Call Jane Updated",
                "description": "Completed follow up",
                "due_date": "2026-09-21",
                "due_time": "11:00",
                "completed": "on",
            },
        )
        self.assertRedirects(
            response,
            reverse("crm:task_detail", args=[task.id]),
        )
        task.refresh_from_db()
        self.assertEqual(task.title, "Call Jane Updated")
        self.assertTrue(task.completed)

        response = self.client.post(
            reverse("crm:task_delete", args=[task.id])
        )
        self.assertRedirects(response, reverse("crm:task_list"))
        self.assertFalse(Task.objects.filter(id=task.id).exists())
