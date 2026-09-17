from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from crm.models import Business, Membership


class CoreViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="coreuser",
            password="TestPass123!",
            email="coreuser@example.com",
        )
        self.business = Business.objects.create(
            name="Core Business",
            slug="core-business",
        )
        Membership.objects.create(
            user=self.user,
            business=self.business,
            role=Membership.ADMIN,
        )

    def test_home_is_public(self):
        response = self.client.get(reverse("core:home"))
        self.assertEqual(response.status_code, 200)

    def test_dashboard_requires_authentication(self):
        response = self.client.get(reverse("core:dashboard"))
        self.assertRedirects(
            response,
            f"{reverse('accounts:login')}?next={reverse('core:dashboard')}",
        )

    def test_help_requires_authentication(self):
        response = self.client.get(reverse("core:help"))
        self.assertRedirects(
            response,
            f"{reverse('accounts:login')}?next={reverse('core:help')}",
        )

    def test_help_is_available_to_authenticated_user(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("core:help"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "How ConnectCRM works")
