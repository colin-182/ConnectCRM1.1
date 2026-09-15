from datetime import timedelta
import secrets

from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from .forms import CompanyForm, ContactForm, DealForm, InvitationForm, TaskForm
from .models import Company, Contact, Deal, Invitation, Membership, Task


def _get_membership(request):
    """Return the logged-in user's ConnectCRM membership, if one exists."""

    return Membership.objects.filter(
        user=request.user
    ).select_related("business").first()


def _get_business(request):
    """Return the business belonging to the logged-in user's membership."""

    membership = _get_membership(request)

    if membership is None:
        return None

    return membership.business


def _set_contact_form_queryset(form, business):
    """Limit contact form company choices to the current business."""

    form.fields["company"].queryset = Company.objects.filter(
        business=business
    )


def _set_deal_form_queryset(form, business):
    """Limit deal form relationship choices to the current business."""

    form.fields["company"].queryset = Company.objects.filter(
        business=business
    )
    form.fields["contact"].queryset = Contact.objects.filter(
        business=business
    )


def _set_task_form_queryset(form, business):
    """Limit task form relationship choices to the current business."""

    form.fields["company"].queryset = Company.objects.filter(
        business=business
    )
    form.fields["contact"].queryset = Contact.objects.filter(
        business=business
    )
    form.fields["deal"].queryset = Deal.objects.filter(
        business=business
    )


# ---------------------------------------------------------------------------
# Companies
# ---------------------------------------------------------------------------


@login_required
def company_list(request):
    """Display companies belonging to the logged-in user's business."""

    business = _get_business(request)

    if business is None:
        return redirect("core:dashboard")

    companies = Company.objects.filter(
        business=business
    )

    return render(
        request,
        "crm/company_list.html",
        {"companies": companies},
    )


@login_required
def company_create(request):
    """Create a new company for the logged-in user's business."""

    business = _get_business(request)

    if business is None:
        return redirect("core:dashboard")

    if request.method == "POST":
        form = CompanyForm(request.POST)

        if form.is_valid():
            company = form.save(commit=False)
            company.business = business
            company.save()

            return redirect("crm:company_list")
    else:
        form = CompanyForm()

    return render(
        request,
        "crm/company_form.html",
        {"form": form},
    )


@login_required
def company_detail(request, company_id):
    """Display a company and its contacts."""

    business = _get_business(request)

    if business is None:
        return redirect("core:dashboard")

    company = get_object_or_404(
        Company,
        id=company_id,
        business=business,
    )

    contacts = Contact.objects.filter(
        company=company,
        business=business,
    )

    return render(
        request,
        "crm/company_detail.html",
        {
            "company": company,
            "contacts": contacts,
        },
    )


@login_required
def company_edit(request, company_id):
    """Edit a company belonging to the logged-in user's business."""

    business = _get_business(request)

    if business is None:
        return redirect("core:dashboard")

    company = get_object_or_404(
        Company,
        id=company_id,
        business=business,
    )

    if request.method == "POST":
        form = CompanyForm(
            request.POST,
            instance=company,
        )

        if form.is_valid():
            form.save()

            return redirect(
                "crm:company_detail",
                company_id=company.id,
            )
    else:
        form = CompanyForm(instance=company)

    return render(
        request,
        "crm/company_form.html",
        {
            "form": form,
            "company": company,
            "is_edit": True,
        },
    )


@login_required
def company_delete(request, company_id):
    """Delete a company belonging to the logged-in user's business."""

    business = _get_business(request)

    if business is None:
        return redirect("core:dashboard")

    company = get_object_or_404(
        Company,
        id=company_id,
        business=business,
    )

    if request.method == "POST":
        company.delete()

        return redirect("crm:company_list")

    return render(
        request,
        "crm/company_confirm_delete.html",
        {"company": company},
    )


# ---------------------------------------------------------------------------
# Contacts
# ---------------------------------------------------------------------------


@login_required
def contact_list(request):
    """Display contacts belonging to the logged-in user's business."""

    business = _get_business(request)

    if business is None:
        return redirect("core:dashboard")

    contacts = Contact.objects.filter(
        business=business
    ).select_related("company")

    return render(
        request,
        "crm/contact_list.html",
        {"contacts": contacts},
    )


@login_required
def contact_create(request):
    """Create a new contact for the logged-in user's business."""

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

            return redirect("crm:contact_list")
    else:
        form = ContactForm()
        _set_contact_form_queryset(form, business)

    return render(
        request,
        "crm/contact_form.html",
        {"form": form},
    )


@login_required
def contact_detail(request, contact_id):
    """Display a contact belonging to the logged-in user's business."""

    business = _get_business(request)

    if business is None:
        return redirect("core:dashboard")

    contact = get_object_or_404(
        Contact.objects.select_related("company"),
        id=contact_id,
        business=business,
    )

    return render(
        request,
        "crm/contact_detail.html",
        {"contact": contact},
    )


@login_required
def contact_edit(request, contact_id):
    """Edit a contact belonging to the logged-in user's business."""

    business = _get_business(request)

    if business is None:
        return redirect("core:dashboard")

    contact = get_object_or_404(
        Contact.objects.select_related("company"),
        id=contact_id,
        business=business,
    )

    if request.method == "POST":
        form = ContactForm(
            request.POST,
            instance=contact,
        )
        _set_contact_form_queryset(form, business)

        if form.is_valid():
            form.save()

            return redirect(
                "crm:contact_detail",
                contact_id=contact.id,
            )
    else:
        form = ContactForm(instance=contact)
        _set_contact_form_queryset(form, business)

    return render(
        request,
        "crm/contact_form.html",
        {
            "form": form,
            "contact": contact,
            "is_edit": True,
        },
    )


@login_required
def contact_delete(request, contact_id):
    """Delete a contact belonging to the logged-in user's business."""

    business = _get_business(request)

    if business is None:
        return redirect("core:dashboard")

    contact = get_object_or_404(
        Contact,
        id=contact_id,
        business=business,
    )

    if request.method == "POST":
        contact.delete()

        return redirect("crm:contact_list")

    return render(
        request,
        "crm/contact_confirm_delete.html",
        {"contact": contact},
    )


# ---------------------------------------------------------------------------
# Deals
# ---------------------------------------------------------------------------


@login_required
def deal_list(request):
    """Display deals belonging to the logged-in user's business."""

    business = _get_business(request)

    if business is None:
        return redirect("core:dashboard")

    deals = Deal.objects.filter(
        business=business
    ).select_related("company", "contact")

    return render(
        request,
        "crm/deal_list.html",
        {"deals": deals},
    )


@login_required
def deal_create(request):
    """Create a new deal for the logged-in user's business."""

    business = _get_business(request)

    if business is None:
        return redirect("core:dashboard")

    if request.method == "POST":
        form = DealForm(request.POST)
        _set_deal_form_queryset(form, business)

        if form.is_valid():
            deal = form.save(commit=False)
            deal.business = business
            deal.save()

            return redirect("crm:deal_list")
    else:
        form = DealForm()
        _set_deal_form_queryset(form, business)

    return render(
        request,
        "crm/deal_form.html",
        {"form": form},
    )


@login_required
def deal_detail(request, deal_id):
    """Display a deal belonging to the logged-in user's business."""

    business = _get_business(request)

    if business is None:
        return redirect("core:dashboard")

    deal = get_object_or_404(
        Deal.objects.select_related("company", "contact"),
        id=deal_id,
        business=business,
    )

    return render(
        request,
        "crm/deal_detail.html",
        {"deal": deal},
    )


@login_required
def deal_edit(request, deal_id):
    """Edit a deal belonging to the logged-in user's business."""

    business = _get_business(request)

    if business is None:
        return redirect("core:dashboard")

    deal = get_object_or_404(
        Deal.objects.select_related("company", "contact"),
        id=deal_id,
        business=business,
    )

    if request.method == "POST":
        form = DealForm(
            request.POST,
            instance=deal,
        )
        _set_deal_form_queryset(form, business)

        if form.is_valid():
            form.save()

            return redirect(
                "crm:deal_detail",
                deal_id=deal.id,
            )
    else:
        form = DealForm(instance=deal)
        _set_deal_form_queryset(form, business)

    return render(
        request,
        "crm/deal_form.html",
        {
            "form": form,
            "deal": deal,
            "is_edit": True,
        },
    )


@login_required
def deal_delete(request, deal_id):
    """Delete a deal belonging to the logged-in user's business."""

    business = _get_business(request)

    if business is None:
        return redirect("core:dashboard")

    deal = get_object_or_404(
        Deal,
        id=deal_id,
        business=business,
    )

    if request.method == "POST":
        deal.delete()

        return redirect("crm:deal_list")

    return render(
        request,
        "crm/deal_confirm_delete.html",
        {"deal": deal},
    )


# ---------------------------------------------------------------------------
# Tasks
# ---------------------------------------------------------------------------


@login_required
def task_list(request):
    """Display tasks belonging to the logged-in user's business."""

    business = _get_business(request)

    if business is None:
        return redirect("core:dashboard")

    tasks = Task.objects.filter(
        business=business
    ).select_related("company", "contact", "deal")

    return render(
        request,
        "crm/task_list.html",
        {"tasks": tasks},
    )


@login_required
def task_create(request):
    """Create a new task for the logged-in user's business."""

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

            return redirect("crm:task_list")
    else:
        form = TaskForm()
        _set_task_form_queryset(form, business)

    return render(
        request,
        "crm/task_form.html",
        {"form": form},
    )


@login_required
def task_detail(request, task_id):
    """Display a task belonging to the logged-in user's business."""

    business = _get_business(request)

    if business is None:
        return redirect("core:dashboard")

    task = get_object_or_404(
        Task.objects.select_related("company", "contact", "deal"),
        id=task_id,
        business=business,
    )

    return render(
        request,
        "crm/task_detail.html",
        {"task": task},
    )


@login_required
def task_edit(request, task_id):
    """Edit a task belonging to the logged-in user's business."""

    business = _get_business(request)

    if business is None:
        return redirect("core:dashboard")

    task = get_object_or_404(
        Task.objects.select_related("company", "contact", "deal"),
        id=task_id,
        business=business,
    )

    if request.method == "POST":
        form = TaskForm(
            request.POST,
            instance=task,
        )
        _set_task_form_queryset(form, business)

        if form.is_valid():
            form.save()

            return redirect(
                "crm:task_detail",
                task_id=task.id,
            )

    else:
        form = TaskForm(instance=task)
        _set_task_form_queryset(form, business)

    return render(
        request,
        "crm/task_form.html",
        {
            "form": form,
            "task": task,
            "is_edit": True,
        },
    )


@login_required
def task_delete(request, task_id):
    """Delete a task belonging to the logged-in user's business."""

    business = _get_business(request)

    if business is None:
        return redirect("core:dashboard")

    task = get_object_or_404(
        Task,
        id=task_id,
        business=business,
    )

    if request.method == "POST":
        task.delete()

        return redirect("crm:task_list")

    return render(
        request,
        "crm/task_confirm_delete.html",
        {"task": task},
    )


# ---------------------------------------------------------------------------
# Invitations
# ---------------------------------------------------------------------------


@login_required
def invitation_create(request):
    """Allow a business administrator to invite a user."""

    membership = _get_membership(request)

    if membership is None:
        return redirect("core:dashboard")

    if membership.role != Membership.ADMIN:
        return redirect("core:dashboard")

    if request.method == "POST":
        form = InvitationForm(request.POST)

        if form.is_valid():
            invitation = form.save(commit=False)

            invitation.business = membership.business
            invitation.token = secrets.token_urlsafe(48)
            invitation.expires_at = timezone.now() + timedelta(days=7)

            invitation.save()

            return redirect("crm:invitation_create")
    else:
        form = InvitationForm()

    return render(
        request,
        "crm/invitation_form.html",
        {
            "form": form,
            "business": membership.business,
        },
    )


def invitation_accept(request, token):
    """Validate an invitation and display the acceptance page."""

    invitation = Invitation.objects.filter(
        token=token,
    ).select_related("business").first()

    if invitation is None:
        return render(
            request,
            "crm/invitation_accept.html",
            {
                "invalid_invitation": True,
            },
        )

    if invitation.is_accepted or invitation.is_expired:
        return render(
            request,
            "crm/invitation_accept.html",
            {
                "invalid_invitation": True,
                "invitation": invitation,
            },
        )

    return render(
        request,
        "crm/invitation_accept.html",
        {
            "invitation": invitation,
            "registration_url": (
                f"{reverse('accounts:register')}"
                f"?invite={invitation.token}"
            ),
        },
    )