from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.shortcuts import render
from django.utils import timezone

from crm.models import Company, Contact, Deal, Membership, Task


def home(request):
    return render(request, "core/home.html")


@login_required
def dashboard(request):
    """Display live CRM statistics and activity for the user's business."""

    membership = Membership.objects.filter(
        user=request.user
    ).select_related("business").first()

    if membership is None:
        return render(
            request,
            "core/dashboard.html",
            {
                "contact_count": 0,
                "active_deal_count": 0,
                "pipeline_value": 0,
                "open_task_count": 0,
                "pipeline": [],
                "upcoming_tasks": [],
                "recent_activity": [],
                "today": timezone.localdate(),
            },
        )

    business = membership.business

    # ------------------------------------------------------------------
    # KPI statistics
    # ------------------------------------------------------------------

    contact_count = Contact.objects.filter(
        business=business
    ).count()

    active_deals = Deal.objects.filter(
        business=business,
        stage__in=[
            Deal.LEAD,
            Deal.QUALIFIED,
            Deal.PROPOSAL,
            Deal.NEGOTIATION,
        ],
    )

    active_deal_count = active_deals.count()

    pipeline_value = active_deals.aggregate(
        total=Sum("value")
    )["total"] or 0

    open_tasks = Task.objects.filter(
        business=business,
        completed=False,
    )

    open_task_count = open_tasks.count()

    # ------------------------------------------------------------------
    # Upcoming tasks
    # ------------------------------------------------------------------

    upcoming_tasks = open_tasks.filter(
        due_date__isnull=False,
        due_date__gte=timezone.localdate(),
    ).select_related(
        "company",
        "contact",
        "deal",
    ).order_by(
        "due_date",
        "due_time",
    )[:4]

    # ------------------------------------------------------------------
    # Sales pipeline
    # ------------------------------------------------------------------

    pipeline = []

    stages = [
        ("LEADS", Deal.LEAD),
        ("QUALIFIED", Deal.QUALIFIED),
        ("PROPOSAL", Deal.PROPOSAL),
        ("NEGOTIATION", Deal.NEGOTIATION),
        ("WON", Deal.WON),
    ]

    for label, stage in stages:
        stage_deals = Deal.objects.filter(
            business=business,
            stage=stage,
        )

        stage_value = stage_deals.aggregate(
            total=Sum("value")
        )["total"] or 0

        pipeline.append(
            {
                "label": label,
                "count": stage_deals.count(),
                "value": stage_value,
            }
        )

    # ------------------------------------------------------------------
    # Recent activity
    # ------------------------------------------------------------------

    recent_activity = []

    companies = Company.objects.filter(
        business=business
    ).order_by("-created_at")[:4]

    for company in companies:
        recent_activity.append(
            {
                "type": "company",
                "icon": "🏢",
                "title": "New company added",
                "description": (
                    f"{company.name} was added to your companies."
                ),
                "timestamp": company.created_at,
            }
        )

    contacts = Contact.objects.filter(
        business=business
    ).order_by("-created_at")[:4]

    for contact in contacts:
        recent_activity.append(
            {
                "type": "contact",
                "icon": "👤",
                "title": "New contact added",
                "description": (
                    f"{contact.first_name} {contact.last_name} "
                    "was added to your contacts."
                ),
                "timestamp": contact.created_at,
            }
        )

    deals = Deal.objects.filter(
        business=business
    ).order_by("-updated_at")[:4]

    for deal in deals:
        recent_activity.append(
            {
                "type": "deal",
                "icon": "↗",
                "title": "Deal updated",
                "description": (
                    f"{deal.title} is currently "
                    f"{deal.get_stage_display().lower()}."
                ),
                "timestamp": deal.updated_at,
            }
        )

    tasks = Task.objects.filter(
        business=business
    ).order_by("-created_at")[:4]

    for task in tasks:
        recent_activity.append(
            {
                "type": "task",
                "icon": "✔️",
                "title": "Task created",
                "description": (
                    f"{task.title} was added to your tasks."
                ),
                "timestamp": task.created_at,
            }
        )

    recent_activity.sort(
        key=lambda activity: activity["timestamp"],
        reverse=True,
    )

    recent_activity = recent_activity[:4]

    return render(
        request,
        "core/dashboard.html",
        {
            "contact_count": contact_count,
            "active_deal_count": active_deal_count,
            "pipeline_value": pipeline_value,
            "open_task_count": open_task_count,
            "pipeline": pipeline,
            "upcoming_tasks": upcoming_tasks,
            "recent_activity": recent_activity,
            "today": timezone.localdate(),
        },
    )