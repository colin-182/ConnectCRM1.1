from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.shortcuts import redirect, render
from django.utils import timezone

from crm.models import Company, Contact, Deal, Membership, Task
from crm.tenancy import build_workspace_url, get_business_and_membership, scope_deals_for_membership


def home(request):
    return render(request, "core/home.html")


@login_required
def help_view(request):
    """Display basic in-app guidance for ConnectCRM users."""

    membership, _tenant_locked = get_business_and_membership(request)
    return render(request, "core/help.html", {"membership": membership})


@login_required
def dashboard(request):
    """Display live CRM statistics and activity for the user's business."""

    membership, tenant_locked = get_business_and_membership(request)

    if membership is None:
        if tenant_locked:
            messages.error(
                request,
                "Your account doesn't have access to this workspace. "
                "Log in with the account your admin invited.",
            )
            return redirect("accounts:login")
        return render(
            request,
            "core/dashboard.html",
            {
                "business": None,
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
    is_admin = membership.role == Membership.ADMIN

    visible_deals = scope_deals_for_membership(Deal.objects.filter(business=business), membership)

    contact_count = Contact.objects.filter(
        business=business
    ).count()

    active_deals = visible_deals.filter(
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

    pipeline = []

    stages = [
        ("LEADS", Deal.LEAD),
        ("QUALIFIED", Deal.QUALIFIED),
        ("PROPOSAL", Deal.PROPOSAL),
        ("NEGOTIATION", Deal.NEGOTIATION),
        ("WON", Deal.WON),
    ]

    for label, stage in stages:
        stage_deals = visible_deals.filter(
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

    # Admins get a per-team-member breakdown of the pipeline so they can
    # drill into any one salesperson's deals (their "granular view").
    team_pipeline = []
    if is_admin:
        User = get_user_model()
        team_members = User.objects.filter(memberships__business=business).distinct().order_by("username")
        for member in team_members:
            member_deals = Deal.objects.filter(business=business, owner=member)
            active_member_deals = member_deals.filter(
                stage__in=[Deal.LEAD, Deal.QUALIFIED, Deal.PROPOSAL, Deal.NEGOTIATION]
            )
            team_pipeline.append(
                {
                    "user_id": member.id,
                    "name": member.get_full_name() or member.username,
                    "deal_count": active_member_deals.count(),
                    "pipeline_value": active_member_deals.aggregate(total=Sum("value"))["total"] or 0,
                }
            )
        unassigned_deals = Deal.objects.filter(business=business, owner__isnull=True)
        active_unassigned = unassigned_deals.filter(
            stage__in=[Deal.LEAD, Deal.QUALIFIED, Deal.PROPOSAL, Deal.NEGOTIATION]
        )
        if active_unassigned.exists():
            team_pipeline.append(
                {
                    "user_id": None,
                    "name": "Unassigned",
                    "deal_count": active_unassigned.count(),
                    "pipeline_value": active_unassigned.aggregate(total=Sum("value"))["total"] or 0,
                }
            )

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
                "description": f"{company.name} was added to your companies.",
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

    deals = visible_deals.order_by("-updated_at")[:4]

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
                "description": f"{task.title} was added to your tasks.",
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
            "business": business,
            "workspace_url": build_workspace_url(request, business),
            "contact_count": contact_count,
            "active_deal_count": active_deal_count,
            "pipeline_value": pipeline_value,
            "open_task_count": open_task_count,
            "pipeline": pipeline,
            "is_admin": is_admin,
            "team_pipeline": team_pipeline,
            "upcoming_tasks": upcoming_tasks,
            "recent_activity": recent_activity,
            "today": timezone.localdate(),
        },
    )
