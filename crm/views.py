from datetime import timedelta
import secrets

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.db import IntegrityError, transaction
from django.db.models import Count, Q, Sum
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme

from .forms import CompanyForm, ContactForm, DealForm, InvitationForm, TaskForm
from .models import Company, Contact, Deal, Invitation, Membership, Task
from .tenancy import get_business_and_membership, scope_deals_for_membership


def _scope_deals_for_membership(queryset, membership):
    return scope_deals_for_membership(queryset, membership)


def _get_membership(request):
    """Return the caller's membership for the active business.

    When the request arrived on a specific business subdomain, only a
    membership in THAT business counts - a member of a different business
    (or no business at all) gets None here, never a stand-in from some
    other workspace they happen to belong to.
    """

    membership, tenant_locked = get_business_and_membership(request)
    if membership is None and tenant_locked:
        messages.error(request, "You don't have access to this workspace.")
    return membership


def _get_business(request):
    membership = _get_membership(request)
    return membership.business if membership else None


def _set_contact_form_queryset(form, business):
    form.fields["company"].queryset = Company.objects.filter(business=business)


def _set_deal_form_queryset(form, business):
    form.fields["company"].queryset = Company.objects.filter(business=business)
    form.fields["contact"].queryset = Contact.objects.filter(business=business)
    if "owner" in form.fields:
        User = get_user_model()
        form.fields["owner"].queryset = User.objects.filter(
            memberships__business=business
        ).distinct().order_by("username")


def _set_task_form_queryset(form, business):
    form.fields["company"].queryset = Company.objects.filter(business=business)
    form.fields["contact"].queryset = Contact.objects.filter(business=business)
    form.fields["deal"].queryset = Deal.objects.filter(business=business)


def _apply_query(queryset, query, fields):
    if not query:
        return queryset
    condition = Q()
    for field in fields:
        condition |= Q(**{f"{field}__icontains": query})
    return queryset.filter(condition)


@login_required
def company_list(request):
    business = _get_business(request)
    if business is None:
        return redirect("core:dashboard")

    query = request.GET.get("q", "").strip()
    companies = Company.objects.filter(business=business).annotate(
        contact_total=Count("contacts", distinct=True),
        deal_total=Count("deals", distinct=True),
    )
    companies = _apply_query(companies, query, ["name", "industry", "email", "phone"])

    return render(request, "crm/company_list.html", {
        "companies": companies,
        "query": query,
        "company_count": companies.count(),
    })


@login_required
def company_create(request):
    business = _get_business(request)
    if business is None:
        return redirect("core:dashboard")

    if request.method == "POST":
        form = CompanyForm(request.POST)
        if form.is_valid():
            company = form.save(commit=False)
            company.business = business
            company.save()
            messages.success(request, f"{company.name} was added to your companies.")
            return redirect("crm:company_list")
    else:
        form = CompanyForm()

    return render(request, "crm/company_form.html", {
        "form": form,
        "is_edit": False,
    })


@login_required
def company_detail(request, company_id):
    business = _get_business(request)
    if business is None:
        return redirect("core:dashboard")

    company = get_object_or_404(Company, id=company_id, business=business)
    contacts = Contact.objects.filter(company=company, business=business)
    deals = Deal.objects.filter(company=company, business=business).select_related("contact")
    tasks = Task.objects.filter(company=company, business=business).select_related("contact", "deal")[:8]

    return render(request, "crm/company_detail.html", {
        "company": company,
        "contacts": contacts,
        "deals": deals,
        "tasks": tasks,
    })


@login_required
def company_edit(request, company_id):
    business = _get_business(request)
    if business is None:
        return redirect("core:dashboard")

    company = get_object_or_404(Company, id=company_id, business=business)
    if request.method == "POST":
        form = CompanyForm(request.POST, instance=company)
        if form.is_valid():
            form.save()
            messages.success(request, f"{company.name} was updated.")
            return redirect("crm:company_detail", company_id=company.id)
    else:
        form = CompanyForm(instance=company)

    return render(request, "crm/company_form.html", {
        "form": form,
        "company": company,
        "is_edit": True,
    })


@login_required
def company_delete(request, company_id):
    business = _get_business(request)
    if business is None:
        return redirect("core:dashboard")
    company = get_object_or_404(Company, id=company_id, business=business)
    if request.method == "POST":
        name = company.name
        company.delete()
        messages.success(request, f"{name} was deleted.")
        return redirect("crm:company_list")
    return render(request, "crm/company_confirm_delete.html", {"company": company})


@login_required
def contact_list(request):
    business = _get_business(request)
    if business is None:
        return redirect("core:dashboard")

    query = request.GET.get("q", "").strip()
    contacts = Contact.objects.filter(business=business).select_related("company")
    if query:
        contacts = contacts.filter(
            Q(first_name__icontains=query)
            | Q(last_name__icontains=query)
            | Q(email__icontains=query)
            | Q(job_title__icontains=query)
            | Q(company__name__icontains=query)
        )

    return render(request, "crm/contact_list.html", {
        "contacts": contacts,
        "query": query,
        "contact_count": contacts.count(),
    })


@login_required
def contact_create(request):
    business = _get_business(request)
    if business is None:
        return redirect("core:dashboard")
    if request.method == "POST":
        form = ContactForm(request.POST)
        _set_contact_form_queryset(form, business)
        if form.is_valid():
            contact = form.save(commit=False)
            contact.business = business
            contact.save()
            messages.success(request, f"{contact.first_name} {contact.last_name} was added to your contacts.")
            return redirect("crm:contact_list")
    else:
        form = ContactForm()
        _set_contact_form_queryset(form, business)
    return render(request, "crm/contact_form.html", {"form": form, "is_edit": False})


@login_required
def contact_detail(request, contact_id):
    business = _get_business(request)
    if business is None:
        return redirect("core:dashboard")
    contact = get_object_or_404(Contact.objects.select_related("company"), id=contact_id, business=business)
    deals = Deal.objects.filter(contact=contact, business=business).select_related("company")
    tasks = Task.objects.filter(contact=contact, business=business).select_related("company", "deal")[:8]
    return render(request, "crm/contact_detail.html", {
        "contact": contact,
        "deals": deals,
        "tasks": tasks,
    })


@login_required
def contact_edit(request, contact_id):
    business = _get_business(request)
    if business is None:
        return redirect("core:dashboard")
    contact = get_object_or_404(Contact.objects.select_related("company"), id=contact_id, business=business)
    if request.method == "POST":
        form = ContactForm(request.POST, instance=contact)
        _set_contact_form_queryset(form, business)
        if form.is_valid():
            form.save()
            messages.success(request, f"{contact.first_name} {contact.last_name} was updated.")
            return redirect("crm:contact_detail", contact_id=contact.id)
    else:
        form = ContactForm(instance=contact)
        _set_contact_form_queryset(form, business)
    return render(request, "crm/contact_form.html", {
        "form": form,
        "contact": contact,
        "is_edit": True,
    })


@login_required
def contact_delete(request, contact_id):
    business = _get_business(request)
    if business is None:
        return redirect("core:dashboard")
    contact = get_object_or_404(Contact, id=contact_id, business=business)
    if request.method == "POST":
        name = f"{contact.first_name} {contact.last_name}"
        contact.delete()
        messages.success(request, f"{name} was deleted.")
        return redirect("crm:contact_list")
    return render(request, "crm/contact_confirm_delete.html", {"contact": contact})


@login_required
def deal_list(request):
    membership = _get_membership(request)
    if membership is None:
        return redirect("core:dashboard")
    business = membership.business
    is_admin = membership.role == Membership.ADMIN

    query = request.GET.get("q", "").strip()
    stage = request.GET.get("stage", "").strip()
    owner_param = request.GET.get("owner", "").strip()
    active_only = request.GET.get("active") == "1"

    visible_deals = _scope_deals_for_membership(
        Deal.objects.filter(business=business), membership
    )

    # Admins get a "granular view" filter to drill into one team member's
    # deals at a time; everyone else is already scoped to their own.
    team_members = None
    if is_admin:
        User = get_user_model()
        team_members = User.objects.filter(memberships__business=business).distinct().order_by("username")
        if owner_param == "unassigned":
            visible_deals = visible_deals.filter(owner__isnull=True)
        elif owner_param.isdigit():
            visible_deals = visible_deals.filter(owner_id=owner_param)

    deals = visible_deals.select_related("company", "contact", "owner")
    if active_only:
        deals = deals.filter(stage__in=[Deal.LEAD, Deal.QUALIFIED, Deal.PROPOSAL, Deal.NEGOTIATION])
    deals = _apply_query(deals, query, ["title", "company__name", "contact__first_name", "contact__last_name"])
    if stage in {choice[0] for choice in Deal.STAGE_CHOICES}:
        deals = deals.filter(stage=stage)

    stage_totals = {
        key: visible_deals.filter(stage=key).aggregate(total=Sum("value"))["total"] or 0
        for key, _ in Deal.STAGE_CHOICES
    }
    pipeline_total = sum(value for key, value in stage_totals.items() if key != Deal.LOST)
    return render(request, "crm/deal_list.html", {
        "deals": deals,
        "query": query,
        "stage": stage,
        "stage_choices": Deal.STAGE_CHOICES,
        "deal_count": deals.count(),
        "pipeline_total": pipeline_total,
        "stage_totals": stage_totals,
        "is_admin": is_admin,
        "team_members": team_members,
        "owner_param": owner_param,
    })


@login_required
def deal_create(request):
    membership = _get_membership(request)
    if membership is None:
        return redirect("core:dashboard")
    business = membership.business
    is_admin = membership.role == Membership.ADMIN
    if request.method == "POST":
        form = DealForm(request.POST, allow_owner_assignment=is_admin)
        _set_deal_form_queryset(form, business)
        if form.is_valid():
            deal = form.save(commit=False)
            deal.business = business
            if is_admin:
                # An admin who didn't pick anyone still gets a sensible
                # default rather than an unassigned deal.
                if not deal.owner_id:
                    deal.owner = request.user
            else:
                deal.owner = request.user
            deal.save()
            messages.success(request, f"{deal.title} was added to your pipeline.")
            return redirect("crm:deal_list")
    else:
        initial = {"owner": request.user.id} if is_admin else None
        form = DealForm(allow_owner_assignment=is_admin, initial=initial)
        _set_deal_form_queryset(form, business)
    return render(request, "crm/deal_form.html", {"form": form, "is_edit": False})


@login_required
def deal_detail(request, deal_id):
    membership = _get_membership(request)
    if membership is None:
        return redirect("core:dashboard")
    deals = _scope_deals_for_membership(Deal.objects.filter(business=membership.business), membership)
    deal = get_object_or_404(deals.select_related("company", "contact", "owner"), id=deal_id)
    tasks = Task.objects.filter(deal=deal, business=membership.business).select_related("company", "contact")
    return render(request, "crm/deal_detail.html", {"deal": deal, "tasks": tasks})


@login_required
def deal_edit(request, deal_id):
    membership = _get_membership(request)
    if membership is None:
        return redirect("core:dashboard")
    business = membership.business
    is_admin = membership.role == Membership.ADMIN
    deals = _scope_deals_for_membership(Deal.objects.filter(business=business), membership)
    deal = get_object_or_404(deals.select_related("company", "contact", "owner"), id=deal_id)
    if request.method == "POST":
        form = DealForm(request.POST, instance=deal, allow_owner_assignment=is_admin)
        _set_deal_form_queryset(form, business)
        if form.is_valid():
            form.save()
            messages.success(request, f"{deal.title} was updated.")
            return redirect("crm:deal_detail", deal_id=deal.id)
    else:
        form = DealForm(instance=deal, allow_owner_assignment=is_admin)
        _set_deal_form_queryset(form, business)
    return render(request, "crm/deal_form.html", {"form": form, "deal": deal, "is_edit": True})


@login_required
def deal_delete(request, deal_id):
    membership = _get_membership(request)
    if membership is None:
        return redirect("core:dashboard")
    deals = _scope_deals_for_membership(Deal.objects.filter(business=membership.business), membership)
    deal = get_object_or_404(deals, id=deal_id)
    if request.method == "POST":
        title = deal.title
        deal.delete()
        messages.success(request, f"{title} was deleted.")
        return redirect("crm:deal_list")
    return render(request, "crm/deal_confirm_delete.html", {"deal": deal})


@login_required
def task_list(request):
    business = _get_business(request)
    if business is None:
        return redirect("core:dashboard")
    query = request.GET.get("q", "").strip()
    status = request.GET.get("status", "open").strip()
    tasks = Task.objects.filter(business=business).select_related("company", "contact", "deal")
    if query:
        tasks = tasks.filter(
            Q(title__icontains=query)
            | Q(description__icontains=query)
            | Q(company__name__icontains=query)
            | Q(contact__first_name__icontains=query)
            | Q(contact__last_name__icontains=query)
            | Q(deal__title__icontains=query)
        )
    if status == "open":
        tasks = tasks.filter(completed=False)
    elif status == "completed":
        tasks = tasks.filter(completed=True)
    return render(request, "crm/task_list.html", {
        "tasks": tasks,
        "query": query,
        "status": status,
        "task_count": tasks.count(),
        "open_total": Task.objects.filter(business=business, completed=False).count(),
        "completed_total": Task.objects.filter(business=business, completed=True).count(),
        "today": timezone.localdate(),
    })


@login_required
def task_create(request):
    business = _get_business(request)
    if business is None:
        return redirect("core:dashboard")
    if request.method == "POST":
        form = TaskForm(request.POST)
        _set_task_form_queryset(form, business)
        if form.is_valid():
            task = form.save(commit=False)
            task.business = business
            task.save()
            messages.success(request, f"{task.title} was added to your tasks.")
            return redirect("crm:task_list")
    else:
        form = TaskForm()
        _set_task_form_queryset(form, business)
    return render(request, "crm/task_form.html", {"form": form, "is_edit": False})


@login_required
def task_detail(request, task_id):
    business = _get_business(request)
    if business is None:
        return redirect("core:dashboard")
    task = get_object_or_404(Task.objects.select_related("company", "contact", "deal"), id=task_id, business=business)
    return render(request, "crm/task_detail.html", {"task": task})


@login_required
def task_edit(request, task_id):
    business = _get_business(request)
    if business is None:
        return redirect("core:dashboard")
    task = get_object_or_404(Task.objects.select_related("company", "contact", "deal"), id=task_id, business=business)
    if request.method == "POST":
        form = TaskForm(request.POST, instance=task)
        _set_task_form_queryset(form, business)
        if form.is_valid():
            form.save()
            messages.success(request, f"{task.title} was updated.")
            return redirect("crm:task_detail", task_id=task.id)
    else:
        form = TaskForm(instance=task)
        _set_task_form_queryset(form, business)
    return render(request, "crm/task_form.html", {"form": form, "task": task, "is_edit": True})


@login_required
def task_toggle(request, task_id):
    business = _get_business(request)
    if business is None:
        return redirect("core:dashboard")
    task = get_object_or_404(Task, id=task_id, business=business)
    if request.method != "POST":
        return redirect("crm:task_detail", task_id=task.id)
    task.completed = not task.completed
    task.save(update_fields=["completed"])
    messages.success(request, f"Task marked {'complete' if task.completed else 'open'}.")
    next_url = request.POST.get("next")
    if url_has_allowed_host_and_scheme(
        next_url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return redirect(next_url)
    return redirect("crm:task_detail", task_id=task.id)


@login_required
def task_delete(request, task_id):
    business = _get_business(request)
    if business is None:
        return redirect("core:dashboard")
    task = get_object_or_404(Task, id=task_id, business=business)
    if request.method == "POST":
        title = task.title
        task.delete()
        messages.success(request, f"{title} was deleted.")
        return redirect("crm:task_list")
    return render(request, "crm/task_confirm_delete.html", {"task": task})


@login_required
def search(request):
    membership = _get_membership(request)
    if membership is None:
        return redirect("core:dashboard")
    business = membership.business
    query = request.GET.get("q", "").strip()
    companies = Company.objects.filter(business=business)
    contacts = Contact.objects.filter(business=business).select_related("company")
    deals = _scope_deals_for_membership(
        Deal.objects.filter(business=business), membership
    ).select_related("company", "contact")
    tasks = Task.objects.filter(business=business).select_related("company", "contact", "deal")
    if query:
        companies = _apply_query(companies, query, ["name", "industry", "email", "phone"])
        contacts = contacts.filter(
            Q(first_name__icontains=query) | Q(last_name__icontains=query)
            | Q(email__icontains=query) | Q(job_title__icontains=query)
            | Q(company__name__icontains=query)
        )
        deals = deals.filter(
            Q(title__icontains=query) | Q(stage__icontains=query)
            | Q(company__name__icontains=query)
            | Q(contact__first_name__icontains=query)
            | Q(contact__last_name__icontains=query)
        )
        tasks = tasks.filter(
            Q(title__icontains=query) | Q(description__icontains=query)
            | Q(company__name__icontains=query)
            | Q(contact__first_name__icontains=query)
            | Q(contact__last_name__icontains=query)
            | Q(deal__title__icontains=query)
        )
    else:
        companies = Company.objects.none()
        contacts = Contact.objects.none()
        deals = Deal.objects.none()
        tasks = Task.objects.none()
    return render(request, "crm/search.html", {
        "query": query,
        "companies": companies[:10],
        "contacts": contacts[:10],
        "deals": deals[:10],
        "tasks": tasks[:10],
    })


@login_required
def search_suggestions(request):
    membership = _get_membership(request)
    if membership is None:
        return JsonResponse({"results": []})
    business = membership.business
    query = request.GET.get("q", "").strip()
    if len(query) < 2:
        return JsonResponse({"results": []})

    results = []
    companies = _apply_query(Company.objects.filter(business=business), query, ["name", "industry"])[:4]
    contacts = Contact.objects.filter(business=business).filter(
        Q(first_name__icontains=query) | Q(last_name__icontains=query) | Q(email__icontains=query)
    ).select_related("company")[:4]
    deals = _scope_deals_for_membership(
        Deal.objects.filter(business=business), membership
    ).filter(
        Q(title__icontains=query) | Q(company__name__icontains=query)
    ).select_related("company")[:4]
    for item in companies:
        results.append({"type": "Company", "title": item.name, "subtitle": item.industry or "Company", "url": reverse("crm:company_detail", args=[item.id])})
    for item in contacts:
        results.append({"type": "Contact", "title": f"{item.first_name} {item.last_name}", "subtitle": item.company.name if item.company else item.job_title or "Contact", "url": reverse("crm:contact_detail", args=[item.id])})
    for item in deals:
        results.append({"type": "Deal", "title": item.title, "subtitle": f"€{item.value:,.2f} · {item.get_stage_display()}", "url": reverse("crm:deal_detail", args=[item.id])})
    return JsonResponse({"results": results[:8]})


@login_required
def invitation_create(request):
    membership = _get_membership(request)
    if membership is None or membership.role != Membership.ADMIN:
        return redirect("core:dashboard")
    if request.method == "POST":
        form = InvitationForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data["email"]
            role = form.cleaned_data["role"]
            existing_pending = Invitation.objects.filter(
                business=membership.business,
                email__iexact=email,
                accepted_at__isnull=True,
                expires_at__gt=timezone.now(),
            ).exists()
            if existing_pending:
                form.add_error("email", "There is already an active invitation for this email address.")
            elif Membership.objects.filter(user__email__iexact=email, business=membership.business).exists():
                form.add_error("email", "This user is already a member of your business.")
            else:
                invitation = form.save(commit=False)
                invitation.business = membership.business
                invitation.role = role
                invitation.token = secrets.token_urlsafe(48)
                invitation.expires_at = timezone.now() + timedelta(days=7)
                invitation.save()
                invitation_url = request.build_absolute_uri(reverse("crm:invitation_accept", args=[invitation.token]))
                subject = f"You're invited to join {membership.business.name} on ConnectCRM"
                body = (
                    f"You've been invited to join {membership.business.name} on ConnectCRM as {invitation.get_role_display()}.\n\n"
                    f"Accept your invitation here:\n{invitation_url}\n\n"
                    f"This invitation expires on {timezone.localtime(invitation.expires_at):%d %B %Y}."
                )
                try:
                    send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, [invitation.email], fail_silently=False)
                except Exception:
                    messages.warning(request, "Invitation created, but the email could not be sent. Use the invitation link below.")
                else:
                    messages.success(request, f"Invitation created and sent to {invitation.email}.")
                return redirect("crm:invitation_create")
    else:
        form = InvitationForm()
    pending_invitations = Invitation.objects.filter(
        business=membership.business,
        accepted_at__isnull=True,
        expires_at__gt=timezone.now(),
    )
    return render(request, "crm/invitation_form.html", {
        "form": form,
        "business": membership.business,
        "pending_invitations": pending_invitations,
    })


def invitation_accept(request, token):
    invitation = Invitation.objects.filter(token=token).select_related("business").first()
    if invitation is None or invitation.is_accepted or invitation.is_expired:
        return render(request, "crm/invitation_accept.html", {"invalid_invitation": True, "invitation": invitation})
    if request.business is not None and invitation.business_id != request.business.id:
        # A token for a different business was used on this subdomain.
        # Treat it the same as an invalid invitation rather than accepting
        # it into whichever business the current subdomain belongs to.
        return render(request, "crm/invitation_accept.html", {"invalid_invitation": True, "invitation": None})
    if request.user.is_authenticated:
        email_matches = request.user.email.lower() == invitation.email.lower()
        if request.method == "POST" and email_matches:
            try:
                with transaction.atomic():
                    locked = Invitation.objects.select_for_update().select_related("business").get(pk=invitation.pk)
                    if locked.is_accepted or locked.is_expired:
                        return render(request, "crm/invitation_accept.html", {"invalid_invitation": True, "invitation": locked})
                    Membership.objects.get_or_create(
                        user=request.user,
                        business=locked.business,
                        defaults={"role": locked.role},
                    )
                    locked.accepted_at = timezone.now()
                    locked.save(update_fields=["accepted_at"])
            except IntegrityError:
                messages.error(request, "We could not accept this invitation. Please try again.")
                return redirect("crm:invitation_accept", token=token)
            messages.success(request, f"You have joined {invitation.business.name}.")
            return redirect("core:dashboard")
        return render(request, "crm/invitation_accept.html", {"invitation": invitation, "email_matches": email_matches})
    return render(request, "crm/invitation_accept.html", {"invitation": invitation})
