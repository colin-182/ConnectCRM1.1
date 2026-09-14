from datetime import timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from crm.models import (
    Business,
    Company,
    Contact,
    Deal,
    Invitation,
    Membership,
    Task,
)


class BusinessIsolationTests(TestCase):
    """Verify that CRM records cannot cross business boundaries."""

    def setUp(self):
        self.business_a = Business.objects.create(
            name="Business A",
            slug="business-a",
        )

        self.business_b = Business.objects.create(
            name="Business B",
            slug="business-b",
        )

        self.user_a = User.objects.create_user(
            username="usera",
            password="TestPass123!",
            email="usera@example.com",
        )

        self.user_b = User.objects.create_user(
            username="userb",
            password="TestPass123!",
            email="userb@example.com",
        )

        Membership.objects.create(
            user=self.user_a,
            business=self.business_a,
            role=Membership.ADMIN,
        )

        Membership.objects.create(
            user=self.user_b,
            business=self.business_b,
            role=Membership.ADMIN,
        )

        self.company_a = Company.objects.create(
            business=self.business_a,
            name="Company A",
        )

        self.company_b = Company.objects.create(
            business=self.business_b,
            name="Company B",
        )

        self.contact_a = Contact.objects.create(
            business=self.business_a,
            company=self.company_a,
            first_name="Contact",
            last_name="A",
        )

        self.contact_b = Contact.objects.create(
            business=self.business_b,
            company=self.company_b,
            first_name="Contact",
            last_name="B",
        )

        self.deal_a = Deal.objects.create(
            business=self.business_a,
            company=self.company_a,
            contact=self.contact_a,
            title="Deal A",
            value=1000,
        )

        self.deal_b = Deal.objects.create(
            business=self.business_b,
            company=self.company_b,
            contact=self.contact_b,
            title="Deal B",
            value=2000,
        )

        self.task_a = Task.objects.create(
            business=self.business_a,
            company=self.company_a,
            contact=self.contact_a,
            deal=self.deal_a,
            title="Task A",
        )

        self.task_b = Task.objects.create(
            business=self.business_b,
            company=self.company_b,
            contact=self.contact_b,
            deal=self.deal_b,
            title="Task B",
        )

        self.client.force_login(self.user_a)

    def test_company_list_only_shows_current_business(self):
        response = self.client.get(
            reverse("crm:company_list")
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertContains(
            response,
            "Company A",
        )

        self.assertNotContains(
            response,
            "Company B",
        )

    def test_contact_list_only_shows_current_business(self):
        response = self.client.get(
            reverse("crm:contact_list")
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertContains(
            response,
            "Contact A",
        )

        self.assertNotContains(
            response,
            "Contact B",
        )

    def test_deal_list_only_shows_current_business(self):
        response = self.client.get(
            reverse("crm:deal_list")
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertContains(
            response,
            "Deal A",
        )

        self.assertNotContains(
            response,
            "Deal B",
        )

    def test_task_list_only_shows_current_business(self):
        response = self.client.get(
            reverse("crm:task_list")
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertContains(
            response,
            "Task A",
        )

        self.assertNotContains(
            response,
            "Task B",
        )

    def test_company_detail_blocks_other_business(self):
        response = self.client.get(
            reverse(
                "crm:company_detail",
                args=[self.company_b.id],
            )
        )

        self.assertEqual(
            response.status_code,
            404,
        )

    def test_contact_detail_blocks_other_business(self):
        response = self.client.get(
            reverse(
                "crm:contact_detail",
                args=[self.contact_b.id],
            )
        )

        self.assertEqual(
            response.status_code,
            404,
        )

    def test_deal_detail_blocks_other_business(self):
        response = self.client.get(
            reverse(
                "crm:deal_detail",
                args=[self.deal_b.id],
            )
        )

        self.assertEqual(
            response.status_code,
            404,
        )

    def test_task_detail_blocks_other_business(self):
        response = self.client.get(
            reverse(
                "crm:task_detail",
                args=[self.task_b.id],
            )
        )

        self.assertEqual(
            response.status_code,
            404,
        )

    def test_company_edit_blocks_other_business(self):
        response = self.client.get(
            reverse(
                "crm:company_edit",
                args=[self.company_b.id],
            )
        )

        self.assertEqual(
            response.status_code,
            404,
        )

    def test_contact_edit_blocks_other_business(self):
        response = self.client.get(
            reverse(
                "crm:contact_edit",
                args=[self.contact_b.id],
            )
        )

        self.assertEqual(
            response.status_code,
            404,
        )

    def test_deal_edit_blocks_other_business(self):
        response = self.client.get(
            reverse(
                "crm:deal_edit",
                args=[self.deal_b.id],
            )
        )

        self.assertEqual(
            response.status_code,
            404,
        )

    def test_task_edit_blocks_other_business(self):
        response = self.client.get(
            reverse(
                "crm:task_edit",
                args=[self.task_b.id],
            )
        )

        self.assertEqual(
            response.status_code,
            404,
        )

    def test_company_delete_blocks_other_business(self):
        response = self.client.get(
            reverse(
                "crm:company_delete",
                args=[self.company_b.id],
            )
        )

        self.assertEqual(
            response.status_code,
            404,
        )

    def test_contact_delete_blocks_other_business(self):
        response = self.client.get(
            reverse(
                "crm:contact_delete",
                args=[self.contact_b.id],
            )
        )

        self.assertEqual(
            response.status_code,
            404,
        )

    def test_deal_delete_blocks_other_business(self):
        response = self.client.get(
            reverse(
                "crm:deal_delete",
                args=[self.deal_b.id],
            )
        )

        self.assertEqual(
            response.status_code,
            404,
        )

    def test_task_delete_blocks_other_business(self):
        response = self.client.get(
            reverse(
                "crm:task_delete",
                args=[self.task_b.id],
            )
        )

        self.assertEqual(
            response.status_code,
            404,
        )


class RelatedObjectSecurityTests(TestCase):
    """Verify that forms cannot attach records from another business."""

    def setUp(self):
        self.business_a = Business.objects.create(
            name="Business A",
            slug="business-a",
        )

        self.business_b = Business.objects.create(
            name="Business B",
            slug="business-b",
        )

        self.user_a = User.objects.create_user(
            username="usera",
            password="TestPass123!",
            email="usera@example.com",
        )

        Membership.objects.create(
            user=self.user_a,
            business=self.business_a,
            role=Membership.ADMIN,
        )

        self.company_b = Company.objects.create(
            business=self.business_b,
            name="Company B",
        )

        self.contact_b = Contact.objects.create(
            business=self.business_b,
            first_name="Contact",
            last_name="B",
        )

        self.deal_b = Deal.objects.create(
            business=self.business_b,
            title="Deal B",
            value=2000,
        )

        self.client.force_login(
            self.user_a
        )

    def test_contact_cannot_use_other_business_company(self):
        response = self.client.post(
            reverse("crm:contact_create"),
            {
                "company": self.company_b.id,
                "first_name": "New",
                "last_name": "Contact",
                "job_title": "Sales",
                "email": "new@example.com",
                "phone": "123456",
            },
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertFalse(
            Contact.objects.filter(
                business=self.business_a,
                first_name="New",
            ).exists()
        )

    def test_deal_cannot_use_other_business_company_or_contact(self):
        response = self.client.post(
            reverse("crm:deal_create"),
            {
                "company": self.company_b.id,
                "contact": self.contact_b.id,
                "title": "Cross Business Deal",
                "value": "5000.00",
                "stage": Deal.LEAD,
            },
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertFalse(
            Deal.objects.filter(
                business=self.business_a,
                title="Cross Business Deal",
            ).exists()
        )

    def test_task_cannot_use_other_business_company_contact_or_deal(self):
        response = self.client.post(
            reverse("crm:task_create"),
            {
                "company": self.company_b.id,
                "contact": self.contact_b.id,
                "deal": self.deal_b.id,
                "title": "Cross Business Task",
                "description": "Should not be created.",
                "due_date": "2026-09-20",
                "due_time": "10:00",
                "completed": "",
            },
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertFalse(
            Task.objects.filter(
                business=self.business_a,
                title="Cross Business Task",
            ).exists()
        )


class InvitationPermissionTests(TestCase):
    """Verify that only business administrators can create invitations."""

    def setUp(self):
        self.business = Business.objects.create(
            name="Business",
            slug="business",
        )

        self.admin = User.objects.create_user(
            username="admin",
            password="TestPass123!",
            email="admin@example.com",
        )

        self.member = User.objects.create_user(
            username="member",
            password="TestPass123!",
            email="member@example.com",
        )

        Membership.objects.create(
            user=self.admin,
            business=self.business,
            role=Membership.ADMIN,
        )

        Membership.objects.create(
            user=self.member,
            business=self.business,
            role=Membership.MEMBER,
        )

    def test_admin_can_create_invitation(self):
        self.client.force_login(
            self.admin
        )

        response = self.client.post(
            reverse("crm:invitation_create"),
            {
                "email": "newuser@example.com",
                "role": Membership.MEMBER,
            },
        )

        self.assertRedirects(
            response,
            reverse("crm:invitation_create"),
        )

        self.assertTrue(
            Invitation.objects.filter(
                business=self.business,
                email="newuser@example.com",
            ).exists()
        )

    def test_non_admin_cannot_create_invitation(self):
        self.client.force_login(
            self.member
        )

        response = self.client.post(
            reverse("crm:invitation_create"),
            {
                "email": "attacker@example.com",
                "role": Membership.MEMBER,
            },
        )

        self.assertRedirects(
            response,
            reverse("core:dashboard"),
        )

        self.assertFalse(
            Invitation.objects.filter(
                email="attacker@example.com",
            ).exists()
        )


class AuthenticationSecurityTests(TestCase):
    """Verify that CRM pages require authentication."""

    def test_unauthenticated_user_is_redirected_to_login(self):
        response = self.client.get(
            reverse("crm:company_list")
        )

        self.assertRedirects(
            response,
            (
                f"{reverse('accounts:login')}"
                f"?next={reverse('crm:company_list')}"
            ),
        )

    def test_invitation_acceptance_is_public(self):
        business = Business.objects.create(
            name="Business",
            slug="business",
        )

        invitation = Invitation.objects.create(
            business=business,
            email="newuser@example.com",
            role=Membership.MEMBER,
            token="test-token-123",
            expires_at=timezone.now() + timedelta(days=7),
        )

        response = self.client.get(
            reverse(
                "crm:invitation_accept",
                args=[invitation.token],
            )
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertContains(
            response,
            "Business",
        )

        self.assertContains(
            response,
            "You're invited",
        )