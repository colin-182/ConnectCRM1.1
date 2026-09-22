from datetime import timedelta

from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from crm.models import Business, Invitation, Membership


class RegistrationTests(TestCase):
    def test_registration_creates_business_membership_and_login(self):
        response = self.client.post(
            reverse("accounts:register"),
            {
                "username": "newuser",
                "email": "newuser@example.com",
                "password1": "StrongPass123!",
                "password2": "StrongPass123!",
            },
        )

        self.assertRedirects(
            response,
            reverse("core:dashboard"),
        )

        user = User.objects.get(username="newuser")
        membership = Membership.objects.get(user=user)

        self.assertEqual(
            user.email,
            "newuser@example.com",
        )
        self.assertEqual(
            membership.role,
            Membership.ADMIN,
        )
        self.assertEqual(
            membership.business.name,
            "newuser's Business",
        )
        self.assertTrue(
            response.wsgi_request.user.is_authenticated
        )

    def test_invited_registration_creates_membership_and_accepts_invitation(self):
        business = Business.objects.create(
            name="Acme Ltd",
            slug="acme-ltd",
        )

        invitation = Invitation.objects.create(
            business=business,
            email="invitee@example.com",
            role=Membership.SALES,
            token="registration-token",
            expires_at=timezone.now() + timedelta(days=7),
        )

        response = self.client.post(
            reverse("accounts:register")
            + "?invitation=registration-token",
            {
                "invitation": invitation.token,
                "username": "invitee",
                "email": "invitee@example.com",
                "password1": "StrongPass123!",
                "password2": "StrongPass123!",
            },
        )

        self.assertRedirects(
            response,
            reverse("core:dashboard"),
        )

        user = User.objects.get(username="invitee")
        membership = Membership.objects.get(user=user)
        invitation.refresh_from_db()

        self.assertEqual(
            membership.business,
            business,
        )
        self.assertEqual(
            membership.role,
            Membership.SALES,
        )
        self.assertIsNotNone(
            invitation.accepted_at,
        )
        self.assertTrue(
            response.wsgi_request.user.is_authenticated
        )

    def test_invited_registration_cannot_change_invitation_email(self):
        business = Business.objects.create(
            name="Acme Ltd",
            slug="acme-ltd",
        )

        invitation = Invitation.objects.create(
            business=business,
            email="invitee@example.com",
            role=Membership.MEMBER,
            token="email-lock-token",
            expires_at=timezone.now() + timedelta(days=7),
        )

        response = self.client.post(
            reverse("accounts:register"),
            {
                "invitation": invitation.token,
                "username": "attacker",
                "email": "attacker@example.com",
                "password1": "StrongPass123!",
                "password2": "StrongPass123!",
            },
        )

        self.assertEqual(
            response.status_code,
            200,
        )
        self.assertFalse(
            User.objects.filter(
                username="attacker"
            ).exists()
        )
        self.assertFalse(
            Membership.objects.filter(
                business=business
            ).exists()
        )

        invitation.refresh_from_db()

        self.assertIsNone(
            invitation.accepted_at
        )


class LoginTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="loginuser",
            password="StrongPass123!",
            email="loginuser@example.com",
        )

    def test_login_redirects_to_safe_next_url(self):
        response = self.client.post(
            reverse("accounts:login"),
            {
                "username": "loginuser",
                "password": "StrongPass123!",
                "next": reverse("core:help"),
            },
        )

        self.assertRedirects(
            response,
            reverse("core:help"),
        )

    def test_login_rejects_external_next_url(self):
        response = self.client.post(
            reverse("accounts:login"),
            {
                "username": "loginuser",
                "password": "StrongPass123!",
                "next": "https://example.com/",
            },
        )

        self.assertRedirects(
            response,
            reverse("core:dashboard"),
        )


class InvitationAcceptanceTests(TestCase):
    def setUp(self):
        self.business = Business.objects.create(
            name="Acme Ltd",
            slug="acme-ltd",
        )

        self.invitation = Invitation.objects.create(
            business=self.business,
            email="invitee@example.com",
            role=Membership.MEMBER,
            token="accept-token",
            expires_at=timezone.now() + timedelta(days=7),
        )

    def test_invitation_page_is_public(self):
        response = self.client.get(
            reverse(
                "crm:invitation_accept",
                args=[self.invitation.token],
            )
        )

        self.assertEqual(
            response.status_code,
            200,
        )
        self.assertContains(
            response,
            "Acme Ltd",
        )
        self.assertContains(
            response,
            "Create account & join",
        )

    def test_logged_in_matching_user_can_accept_invitation(self):
        user = User.objects.create_user(
            username="invitee",
            password="StrongPass123!",
            email="INVITEE@example.com",
        )

        self.client.force_login(user)

        response = self.client.post(
            reverse(
                "crm:invitation_accept",
                args=[self.invitation.token],
            )
        )

        self.assertRedirects(
            response,
            reverse("core:dashboard"),
        )

        self.invitation.refresh_from_db()

        self.assertIsNotNone(
            self.invitation.accepted_at
        )
        self.assertTrue(
            Membership.objects.filter(
                user=user,
                business=self.business,
                role=Membership.MEMBER,
            ).exists()
        )

    def test_logged_in_wrong_user_cannot_accept_invitation(self):
        user = User.objects.create_user(
            username="wronguser",
            password="StrongPass123!",
            email="wrong@example.com",
        )

        self.client.force_login(user)

        response = self.client.post(
            reverse(
                "crm:invitation_accept",
                args=[self.invitation.token],
            )
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.invitation.refresh_from_db()

        self.assertIsNone(
            self.invitation.accepted_at
        )
        self.assertFalse(
            Membership.objects.filter(
                user=user,
                business=self.business,
            ).exists()
        )

    def test_accepted_invitation_cannot_be_reused(self):
        self.invitation.accepted_at = timezone.now()
        self.invitation.save(
            update_fields=["accepted_at"]
        )

        response = self.client.get(
            reverse(
                "crm:invitation_accept",
                args=[self.invitation.token],
            )
        )

        self.assertEqual(
            response.status_code,
            200,
        )
        self.assertContains(
            response,
            "Invitation unavailable",
        )

    def test_expired_invitation_cannot_be_used(self):
        self.invitation.expires_at = (
            timezone.now() - timedelta(minutes=1)
        )
        self.invitation.save(
            update_fields=["expires_at"]
        )

        response = self.client.get(
            reverse(
                "crm:invitation_accept",
                args=[self.invitation.token],
            )
        )

        self.assertEqual(
            response.status_code,
            200,
        )
        self.assertContains(
            response,
            "Invitation unavailable",
        )


@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend"
)
class InvitationEmailTests(TestCase):
    def setUp(self):
        self.business = Business.objects.create(
            name="Acme Ltd",
            slug="acme-ltd",
        )

        self.admin = User.objects.create_user(
            username="admin",
            password="StrongPass123!",
            email="admin@example.com",
        )

        Membership.objects.create(
            user=self.admin,
            business=self.business,
            role=Membership.ADMIN,
        )

        self.client.force_login(self.admin)

    def test_creating_invitation_sends_email_with_acceptance_link(self):
        response = self.client.post(
            reverse("crm:invitation_create"),
            {
                "email": "newmember@example.com",
                "role": Membership.SALES,
            },
        )

        self.assertRedirects(
            response,
            reverse("crm:invitation_create"),
        )

        self.assertEqual(
            len(mail.outbox),
            1,
        )

        self.assertIn(
            "Acme Ltd",
            mail.outbox[0].subject,
        )
        self.assertIn(
            "/crm/invitations/",
            mail.outbox[0].body,
        )
        self.assertIn(
            "newmember@example.com",
            mail.outbox[0].to,
        )


@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend"
)
class PasswordResetTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="resetuser",
            password="OldStrongPass123!",
            email="resetuser@example.com",
        )

    def test_password_reset_request_sends_email(self):
        response = self.client.post(
            reverse("accounts:password_reset"),
            {
                "email": "resetuser@example.com",
            },
        )

        self.assertRedirects(
            response,
            reverse("accounts:password_reset_done"),
        )

        self.assertEqual(
            len(mail.outbox),
            1,
        )

        self.assertEqual(
            mail.outbox[0].subject,
            "Reset your ConnectCRM password",
        )

        self.assertIn(
            "resetuser@example.com",
            mail.outbox[0].to,
        )

        self.assertIn(
            "/accounts/reset/",
            mail.outbox[0].body,
        )

        self.assertIn(
            "create a new password",
            mail.outbox[0].body,
        )

    def test_password_reset_request_does_not_reveal_unknown_email(self):
        response = self.client.post(
            reverse("accounts:password_reset"),
            {
                "email": "does-not-exist@example.com",
            },
        )

        self.assertRedirects(
            response,
            reverse("accounts:password_reset_done"),
        )

        self.assertEqual(
            len(mail.outbox),
            0,
        )

    def test_password_reset_link_allows_password_change(self):
        self.client.post(
            reverse("accounts:password_reset"),
            {
                "email": "resetuser@example.com",
            },
        )

        self.assertEqual(
            len(mail.outbox),
            1,
        )

        email_body = mail.outbox[0].body

        uidb64 = urlsafe_base64_encode(
            force_bytes(self.user.pk)
        )

        token = default_token_generator.make_token(
            self.user
        )

        reset_path = reverse(
            "accounts:password_reset_confirm",
            kwargs={
                "uidb64": uidb64,
                "token": token,
            },
        )

        self.assertIn(
            reset_path,
            email_body,
        )

        # Django's PasswordResetConfirmView redirects the first
        # request to the same URL with a password-reset marker.
        response = self.client.get(
            reset_path,
        )

        self.assertEqual(
            response.status_code,
            302,
        )

        reset_url = response.url

        self.assertIn(
            "set-password",
            reset_url,
        )

        response = self.client.get(
            reset_url,
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertContains(
            response,
            "Create a new password",
        )

        response = self.client.post(
            reset_url,
            {
                "new_password1": "NewStrongPass123!",
                "new_password2": "NewStrongPass123!",
            },
        )

        self.assertRedirects(
            response,
            reverse("accounts:password_reset_complete"),
        )

        self.user.refresh_from_db()

        self.assertTrue(
            self.user.check_password(
                "NewStrongPass123!"
            )
        )

    def test_password_reset_confirm_page_rejects_invalid_link(self):
        response = self.client.get(
            reverse(
                "accounts:password_reset_confirm",
                kwargs={
                    "uidb64": "MQ",
                    "token": "invalid-token",
                },
            )
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertContains(
            response,
            "Invalid reset link",
        )