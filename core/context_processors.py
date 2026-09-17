from django.conf import settings
from django.urls import reverse
from django.utils import timezone

from crm.models import Invitation, Membership, Task
from crm.tenancy import get_business_and_membership


def crm_header(request):
    """Provide header data without requiring every view to duplicate it."""
    base = {
        "header_notifications": [],
        "header_notification_count": 0,
        "header_membership": None,
        "base_domain": settings.BASE_DOMAIN,
    }

    if not getattr(request, "user", None) or not request.user.is_authenticated:
        return base

    # On a business subdomain, only that business's membership is
    # relevant here - a mismatch is handled (and messaged) by the view
    # itself, so the header should just stay empty rather than showing
    # data for some other business the user belongs to.
    membership, tenant_locked = get_business_and_membership(request)
    if membership is None:
        return base

    business = membership.business
    today = timezone.localdate()
    notifications = []

    overdue = Task.objects.filter(
        business=business,
        completed=False,
        due_date__lt=today,
    ).order_by("due_date")[:3]
    for task in overdue:
        notifications.append({
            "title": "Overdue task",
            "description": task.title,
            "url": reverse("crm:task_detail", args=[task.id]),
            "kind": "danger",
        })

    due_today = Task.objects.filter(
        business=business,
        completed=False,
        due_date=today,
    ).order_by("due_time")[:3]
    for task in due_today:
        notifications.append({
            "title": "Task due today",
            "description": task.title,
            "url": reverse("crm:task_detail", args=[task.id]),
            "kind": "warning",
        })

    if membership.role == Membership.ADMIN:
        pending = Invitation.objects.filter(
            business=business,
            accepted_at__isnull=True,
            expires_at__gt=timezone.now(),
        ).count()
        if pending:
            notifications.append({
                "title": "Pending invitations",
                "description": f"{pending} team invitation{'s' if pending != 1 else ''} awaiting acceptance",
                "url": reverse("crm:invitation_create"),
                "kind": "info",
            })

    notifications = notifications[:6]
    return {
        "header_notifications": notifications,
        "header_notification_count": len(notifications),
        "header_membership": membership,
        "base_domain": settings.BASE_DOMAIN,
    }
