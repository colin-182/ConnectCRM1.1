from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from crm.models import Business, Company, Contact, Deal, Membership, Task


class SearchIsolationTests(TestCase):
    def setUp(self):
        self.business_a = Business.objects.create(
            name="Business A",
            slug="business-a",
        )
        self.business_b = Business.objects.create(
            name="Business B",
            slug="business-b",
        )
        self.user = User.objects.create_user(
            username="usera",
            password="TestPass123!",
            email="usera@example.com",
        )
        Membership.objects.create(
            user=self.user,
            business=self.business_a,
            role=Membership.ADMIN,
        )

        self.company_a = Company.objects.create(
            business=self.business_a,
            name="Shared Search Company",
        )
        Company.objects.create(
            business=self.business_b,
            name="Shared Search Company",
        )

        self.contact_a = Contact.objects.create(
            business=self.business_a,
            first_name="Shared",
            last_name="Contact",
        )
        Contact.objects.create(
            business=self.business_b,
            first_name="Shared",
            last_name="Contact",
        )

        self.deal_a = Deal.objects.create(
            business=self.business_a,
            title="Shared Search Deal",
            value=1000,
        )
        Deal.objects.create(
            business=self.business_b,
            title="Shared Search Deal",
            value=2000,
        )

        self.task_a = Task.objects.create(
            business=self.business_a,
            title="Shared Search Task",
        )
        Task.objects.create(
            business=self.business_b,
            title="Shared Search Task",
        )

        self.client.force_login(self.user)

    def test_search_returns_current_business_records_only(self):
        response = self.client.get(
            reverse("crm:search"),
            {"q": "Shared Search"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            list(response.context["companies"]),
            [self.company_a],
        )
        self.assertEqual(
            list(response.context["deals"]),
            [self.deal_a],
        )
        self.assertEqual(
            list(response.context["tasks"]),
            [self.task_a],
        )

    def test_search_requires_authentication(self):
        self.client.logout()

        response = self.client.get(reverse("crm:search"))

        self.assertRedirects(
            response,
            f"{reverse('accounts:login')}?next={reverse('crm:search')}",
        )
