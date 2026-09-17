from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from crm.models import Business, Deal, Membership


class DealOwnershipTests(TestCase):
    """Verify per-salesperson deal scoping and the admin/manager granular view."""

    def setUp(self):
        self.business = Business.objects.create(name="Team Co", slug="team-co")

        self.admin = User.objects.create_user(username="manager", password="TestPass123!")
        Membership.objects.create(user=self.admin, business=self.business, role=Membership.ADMIN)

        self.rep_a = User.objects.create_user(username="repa", password="TestPass123!")
        Membership.objects.create(user=self.rep_a, business=self.business, role=Membership.SALES)

        self.rep_b = User.objects.create_user(username="repb", password="TestPass123!")
        Membership.objects.create(user=self.rep_b, business=self.business, role=Membership.SALES)

        self.deal_a = Deal.objects.create(business=self.business, title="Deal A", value=1000, owner=self.rep_a)
        self.deal_b = Deal.objects.create(business=self.business, title="Deal B", value=2000, owner=self.rep_b)
        self.unassigned = Deal.objects.create(business=self.business, title="Unassigned Deal", value=500)

    def test_sales_rep_only_sees_own_and_unassigned_deals(self):
        self.client.force_login(self.rep_a)
        response = self.client.get(reverse("crm:deal_list"))
        titles = {deal.title for deal in response.context["deals"]}
        self.assertEqual(titles, {"Deal A", "Unassigned Deal"})

    def test_admin_sees_every_deal_by_default(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse("crm:deal_list"))
        titles = {deal.title for deal in response.context["deals"]}
        self.assertEqual(titles, {"Deal A", "Deal B", "Unassigned Deal"})

    def test_admin_can_filter_to_one_team_members_deals(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse("crm:deal_list"), {"owner": self.rep_b.id})
        titles = {deal.title for deal in response.context["deals"]}
        self.assertEqual(titles, {"Deal B"})

    def test_sales_rep_cannot_open_a_teammates_deal_directly(self):
        self.client.force_login(self.rep_a)
        response = self.client.get(reverse("crm:deal_detail", args=[self.deal_b.id]))
        self.assertEqual(response.status_code, 404)

    def test_sales_rep_cannot_edit_a_teammates_deal_directly(self):
        self.client.force_login(self.rep_a)
        response = self.client.post(
            reverse("crm:deal_edit", args=[self.deal_b.id]),
            {"title": "Hijacked", "value": 1, "stage": Deal.LEAD},
        )
        self.assertEqual(response.status_code, 404)
        self.deal_b.refresh_from_db()
        self.assertEqual(self.deal_b.title, "Deal B")

    def test_sales_rep_can_open_their_own_deal(self):
        self.client.force_login(self.rep_a)
        response = self.client.get(reverse("crm:deal_detail", args=[self.deal_a.id]))
        self.assertEqual(response.status_code, 200)

    def test_new_deal_created_by_sales_rep_is_auto_assigned_to_them(self):
        self.client.force_login(self.rep_a)
        self.client.post(
            reverse("crm:deal_create"),
            {"title": "Fresh Lead", "value": 300, "stage": Deal.LEAD},
        )
        deal = Deal.objects.get(title="Fresh Lead")
        self.assertEqual(deal.owner, self.rep_a)

    def test_sales_rep_cannot_reassign_owner_via_form_tampering(self):
        # The owner field isn't rendered for non-admins at all, so even a
        # crafted POST including an "owner" key must not be able to
        # reassign a deal to someone else.
        self.client.force_login(self.rep_a)
        self.client.post(
            reverse("crm:deal_edit", args=[self.deal_a.id]),
            {"title": "Deal A", "value": 1000, "stage": Deal.LEAD, "owner": self.rep_b.id},
        )
        self.deal_a.refresh_from_db()
        self.assertEqual(self.deal_a.owner, self.rep_a)

    def test_admin_can_assign_deal_to_a_team_member(self):
        self.client.force_login(self.admin)
        self.client.post(
            reverse("crm:deal_edit", args=[self.unassigned.id]),
            {"title": "Unassigned Deal", "value": 500, "stage": Deal.LEAD, "owner": self.rep_b.id},
        )
        self.unassigned.refresh_from_db()
        self.assertEqual(self.unassigned.owner, self.rep_b)

    def test_dashboard_active_deal_count_is_scoped_for_sales_rep(self):
        self.client.force_login(self.rep_a)
        response = self.client.get(reverse("core:dashboard"))
        # rep_a owns 1 active deal (Deal A) + sees the 1 unassigned deal = 2
        self.assertEqual(response.context["active_deal_count"], 2)

    def test_dashboard_shows_team_pipeline_panel_for_admin_only(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse("core:dashboard"))
        self.assertTrue(response.context["is_admin"])
        names = {row["name"] for row in response.context["team_pipeline"]}
        self.assertIn("repa", names)
        self.assertIn("repb", names)

        self.client.force_login(self.rep_a)
        response = self.client.get(reverse("core:dashboard"))
        self.assertFalse(response.context["is_admin"])
