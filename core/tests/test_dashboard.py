from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from crm.models import Business, Company, Contact, Deal, Membership, Task


class DashboardTests(TestCase):
    def setUp(self):
        self.business = Business.objects.create(
            name="Dashboard Business",
            slug="dashboard-business",
        )
        self.user = User.objects.create_user(
            username="dashboarduser",
            password="TestPass123!",
            email="dashboard@example.com",
        )
        Membership.objects.create(
            user=self.user,
            business=self.business,
            role=Membership.ADMIN,
        )
        self.client.force_login(self.user)

    def test_dashboard_shows_business_kpis(self):
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
        Deal.objects.create(
            business=self.business,
            company=company,
            contact=contact,
            title="Open Deal",
            value=2500,
            stage=Deal.PROPOSAL,
        )
        Deal.objects.create(
            business=self.business,
            title="Won Deal",
            value=5000,
            stage=Deal.WON,
        )
        Task.objects.create(
            business=self.business,
            title="Follow up",
            completed=False,
        )

        response = self.client.get(reverse("core:dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["contact_count"], 1)
        self.assertEqual(response.context["active_deal_count"], 1)
        self.assertEqual(response.context["pipeline_value"], 2500)
        self.assertEqual(response.context["open_task_count"], 1)
        self.assertContains(response, "Dashboard Business")
