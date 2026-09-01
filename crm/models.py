from django.contrib.auth.models import User
from django.db import models


class Business(models.Model):
    """Represents a business using ConnectCRM."""

    name = models.CharField(max_length=150)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Membership(models.Model):
    """Links a Django user to a business and defines their CRM role."""

    ADMIN = "admin"
    SALES = "sales"
    MEMBER = "member"

    ROLE_CHOICES = [
        (ADMIN, "Admin"),
        (SALES, "Sales"),
        (MEMBER, "Member"),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="memberships",
    )
    business = models.ForeignKey(
        Business,
        on_delete=models.CASCADE,
        related_name="memberships",
    )
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default=MEMBER,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "business"],
                name="unique_user_business_membership",
            )
        ]

    def __str__(self):
        return f"{self.user.username} - {self.business.name}"


class Company(models.Model):
    """Stores a company belonging to a ConnectCRM business."""

    business = models.ForeignKey(
        Business,
        on_delete=models.CASCADE,
        related_name="companies",
    )
    name = models.CharField(max_length=150)
    industry = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=50, blank=True)
    email = models.EmailField(blank=True)
    website = models.URLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Contact(models.Model):
    """Stores an individual contact belonging to a ConnectCRM business."""

    business = models.ForeignKey(
        Business,
        on_delete=models.CASCADE,
        related_name="contacts",
    )
    company = models.ForeignKey(
        Company,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="contacts",
    )
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    job_title = models.CharField(max_length=100, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["last_name", "first_name"]

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class Deal(models.Model):
    """Stores a sales opportunity belonging to a ConnectCRM business."""

    LEAD = "lead"
    QUALIFIED = "qualified"
    PROPOSAL = "proposal"
    NEGOTIATION = "negotiation"
    WON = "won"
    LOST = "lost"

    STAGE_CHOICES = [
        (LEAD, "Lead"),
        (QUALIFIED, "Qualified"),
        (PROPOSAL, "Proposal"),
        (NEGOTIATION, "Negotiation"),
        (WON, "Won"),
        (LOST, "Lost"),
    ]

    business = models.ForeignKey(
        Business,
        on_delete=models.CASCADE,
        related_name="deals",
    )
    company = models.ForeignKey(
        Company,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="deals",
    )
    contact = models.ForeignKey(
        Contact,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="deals",
    )
    title = models.CharField(max_length=200)
    value = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
    )
    stage = models.CharField(
        max_length=20,
        choices=STAGE_CHOICES,
        default=LEAD,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self):
        return self.title


class Task(models.Model):
    """Stores an action or follow-up belonging to a ConnectCRM business."""

    business = models.ForeignKey(
        Business,
        on_delete=models.CASCADE,
        related_name="tasks",
    )
    company = models.ForeignKey(
        Company,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="tasks",
    )
    contact = models.ForeignKey(
        Contact,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="tasks",
    )
    deal = models.ForeignKey(
        Deal,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="tasks",
    )
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    due_date = models.DateTimeField(null=True, blank=True)
    completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["completed", "due_date", "-created_at"]

    def __str__(self):
        return self.title