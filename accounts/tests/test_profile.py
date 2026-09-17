from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from crm.models import Business, Membership


class ProfileTests(TestCase):
    def setUp(self):
        self.business = Business.objects.create(name="Profile Business", slug="profile-business")
        self.user = User.objects.create_user(
            username="profileuser",
            password="StrongPass123!",
            email="profile@example.com",
        )
        Membership.objects.create(
            user=self.user,
            business=self.business,
            role=Membership.ADMIN,
        )

    def test_profile_requires_login(self):
        response = self.client.get(reverse("accounts:profile"))
        self.assertRedirects(
            response,
            f"{reverse('accounts:login')}?next={reverse('accounts:profile')}",
        )

    def test_profile_shows_account_and_membership(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("accounts:profile"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "profileuser")
        self.assertContains(response, "Profile Business")
        self.assertContains(response, "Admin")
