from django.conf import settings
from django.db import models


class Business(models.Model):
    """A business account that owns CRM records."""

    name = models.CharField(
        max_length=200,
    )

    slug = models.SlugField(
        max_length=100,
        unique=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Membership(models.Model):
    """Connect a user to a business with a specific role."""

    ADMIN = "admin"
    SALES = "sales"
    MEMBER = "member"

    ROLE_CHOICES = [
        (ADMIN, "Admin"),
        (SALES, "Sales"),
        (MEMBER, "Member"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
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


class Invitation(models.Model):
    """An invitation for a user to join a specific business."""

    business = models.ForeignKey(
        Business,
        on_delete=models.CASCADE,
        related_name="invitations",
    )

    email = models.EmailField()

    role = models.CharField(
        max_length=20,
        choices=Membership.ROLE_CHOICES,
        default=Membership.MEMBER,
    )

    token = models.CharField(
        max_length=64,
        unique=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    expires_at = models.DateTimeField()

    accepted_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.email} - {self.business.name}"

    @property
    def is_accepted(self):
        """Return whether the invitation has already been accepted."""

        return self.accepted_at is not None

    @property
    def is_expired(self):
        """Return whether the invitation has passed its expiry time."""

        from django.utils import timezone

        return timezone.now() >= self.expires_at
        

class Company(models.Model):
    """A company belonging to a business."""

    business = models.ForeignKey(
        Business,
        on_delete=models.CASCADE,
        related_name="companies",
    )

    name = models.CharField(
        max_length=200,
    )

    industry = models.CharField(
        max_length=100,
        blank=True,
    )

    phone = models.CharField(
        max_length=50,
        blank=True,
    )

    email = models.EmailField(
        blank=True,
    )

    website = models.URLField(
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Contact(models.Model):
    """A contact belonging to a business and optionally linked to a company."""

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

    first_name = models.CharField(
        max_length=100,
    )

    last_name = models.CharField(
        max_length=100,
    )

    job_title = models.CharField(
        max_length=150,
        blank=True,
    )

    email = models.EmailField(
        blank=True,
    )

    phone = models.CharField(
        max_length=50,
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        ordering = ["last_name", "first_name"]

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class Deal(models.Model):
    """A sales opportunity belonging to a business."""

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

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="deals",
        help_text="The team member this deal belongs to.",
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

    title = models.CharField(
        max_length=200,
    )

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

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self):
        return self.title

    @property
    def owner_display(self):
        """A safe, always-renderable label for who owns this deal."""

        if self.owner_id is None:
            return "Unassigned"
        return self.owner.get_full_name() or self.owner.username


class Task(models.Model):
    """A CRM task that can be associated with companies, contacts and deals."""

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

    title = models.CharField(
        max_length=200,
    )

    description = models.TextField(
        blank=True,
    )

    due_date = models.DateField(
        null=True,
        blank=True,
    )

    due_time = models.TimeField(
        null=True,
        blank=True,
    )

    completed = models.BooleanField(
        default=False,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        ordering = ["due_date", "due_time", "-created_at"]

    def __str__(self):
        return self.title