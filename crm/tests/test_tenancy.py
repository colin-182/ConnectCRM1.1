from django.conf import settings
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from crm.models import Business, Company, Membership


def host_for(slug):
    return f"{slug}.{settings.BASE_DOMAIN}"


class TenantMiddlewareTests(TestCase):
    """Verify subdomain resolution and workspace isolation end to end."""

    def setUp(self):
        self.business_a = Business.objects.create(name="Business A", slug="business-a")
        self.business_b = Business.objects.create(name="Business B", slug="business-b")

        self.user_a = User.objects.create_user(
            username="usera", password="StrongPass123!", email="usera@example.com"
        )
        Membership.objects.create(user=self.user_a, business=self.business_a, role=Membership.ADMIN)

        self.user_b = User.objects.create_user(
            username="userb", password="StrongPass123!", email="userb@example.com"
        )
        Membership.objects.create(user=self.user_b, business=self.business_b, role=Membership.ADMIN)

        Company.objects.create(business=self.business_a, name="Alpha Corp")
        Company.objects.create(business=self.business_b, name="Beta Corp")

    def test_unknown_subdomain_returns_404(self):
        response = self.client.get(reverse("core:home"), HTTP_HOST=host_for("no-such-business"))
        self.assertEqual(response.status_code, 404)

    def test_reserved_subdomain_behaves_like_root_domain(self):
        response = self.client.get(reverse("core:home"), HTTP_HOST=host_for("www"))
        self.assertEqual(response.status_code, 200)

    def test_member_sees_only_their_business_on_matching_subdomain(self):
        self.client.login(username="usera", password="StrongPass123!")
        response = self.client.get(reverse("crm:company_list"), HTTP_HOST=host_for("business-a"))
        self.assertEqual(response.status_code, 200)
        companies = list(response.context["companies"])
        self.assertEqual([c.name for c in companies], ["Alpha Corp"])

    def test_non_member_is_denied_on_someone_elses_subdomain(self):
        # user_a is only a member of business_a, but visits business_b's
        # workspace. They must NOT see business_b's data, and must not be
        # quietly bounced into their own business_a data either -
        # the URL they're on should mean something.
        self.client.login(username="usera", password="StrongPass123!")
        response = self.client.get(reverse("crm:company_list"), HTTP_HOST=host_for("business-b"))
        self.assertNotEqual(response.status_code, 200)

    def test_dashboard_denies_non_member_on_wrong_subdomain(self):
        self.client.login(username="usera", password="StrongPass123!")
        response = self.client.get(reverse("core:dashboard"), HTTP_HOST=host_for("business-b"))
        self.assertRedirects(
            response,
            reverse("accounts:login"),
            fetch_redirect_response=False,
        )

    def test_login_rejected_with_correct_password_but_wrong_workspace(self):
        response = self.client.post(
            reverse("accounts:login"),
            {"username": "usera", "password": "StrongPass123!"},
            HTTP_HOST=host_for("business-b"),
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("doesn't have access", response.context["error"])
        self.assertFalse(response.wsgi_request.user.is_authenticated)

    def test_login_succeeds_for_matching_workspace(self):
        response = self.client.post(
            reverse("accounts:login"),
            {"username": "usera", "password": "StrongPass123!"},
            HTTP_HOST=host_for("business-a"),
        )
        self.assertRedirects(
            response,
            reverse("core:dashboard"),
            fetch_redirect_response=False,
        )

    def test_root_domain_falls_back_to_users_own_business(self):
        self.client.login(username="usera", password="StrongPass123!")
        response = self.client.get(reverse("crm:company_list"), HTTP_HOST=settings.BASE_DOMAIN)
        self.assertEqual(response.status_code, 200)
        companies = list(response.context["companies"])
        self.assertEqual([c.name for c in companies], ["Alpha Corp"])

    def test_new_business_cannot_be_created_from_inside_another_workspace(self):
        response = self.client.post(
            reverse("accounts:register"),
            {
                "username": "sneaky",
                "email": "sneaky@example.com",
                "password1": "StrongPass123!",
                "password2": "StrongPass123!",
            },
            HTTP_HOST=host_for("business-a"),
        )
        self.assertEqual(response.status_code, 302)
        self.assertFalse(User.objects.filter(username="sneaky").exists())
