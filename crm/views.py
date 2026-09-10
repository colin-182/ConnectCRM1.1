from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .forms import CompanyForm, ContactForm, DealForm, TaskForm
from .models import Company, Contact, Deal, Membership, Task


# ---------------------------------------------------------------------------
# Companies
# ---------------------------------------------------------------------------


@login_required
def company_list(request):
    """Display companies belonging to the logged-in user's business."""

    memberships = Membership.objects.filter(
        user=request.user
    ).select_related("business")

    companies = Company.objects.filter(
        business__in=memberships.values("business")
    )

    return render(
        request,
        "crm/company_list.html",
        {"companies": companies},
    )


@login_required
def company_create(request):
    """Create a new company for the logged-in user's business."""

    membership = Membership.objects.filter(
        user=request.user
    ).select_related("business").first()

    if membership is None:
        return redirect("core:dashboard")

    if request.method == "POST":
        form = CompanyForm(request.POST)

        if form.is_valid():
            company = form.save(commit=False)
            company.business = membership.business
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

    membership = Membership.objects.filter(
        user=request.user
    ).select_related("business").first()

    if membership is None:
        return redirect("core:dashboard")

    company = Company.objects.filter(
        id=company_id,
        business=membership.business,
    ).first()

    if company is None:
        return redirect("crm:company_list")

    contacts = Contact.objects.filter(
        company=company,
        business=membership.business,
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

    membership = Membership.objects.filter(
        user=request.user
    ).select_related("business").first()

    if membership is None:
        return redirect("core:dashboard")

    company = Company.objects.filter(
        id=company_id,
        business=membership.business,
    ).first()

    if company is None:
        return redirect("crm:company_list")

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

    membership = Membership.objects.filter(
        user=request.user
    ).select_related("business").first()

    if membership is None:
        return redirect("core:dashboard")

    company = Company.objects.filter(
        id=company_id,
        business=membership.business,
    ).first()

    if company is None:
        return redirect("crm:company_list")

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

    memberships = Membership.objects.filter(
        user=request.user
    ).select_related("business")

    contacts = Contact.objects.filter(
        business__in=memberships.values("business")
    ).select_related("company")

    return render(
        request,
        "crm/contact_list.html",
        {"contacts": contacts},
    )


@login_required
def contact_create(request):
    """Create a new contact for the logged-in user's business."""

    membership = Membership.objects.filter(
        user=request.user
    ).select_related("business").first()

    if membership is None:
        return redirect("core:dashboard")

    if request.method == "POST":
        form = ContactForm(request.POST)

        # Only show companies belonging to the user's business.
        form.fields["company"].queryset = Company.objects.filter(
            business=membership.business
        )

        if form.is_valid():
            contact = form.save(commit=False)
            contact.business = membership.business
            contact.save()

            return redirect("crm:contact_list")
    else:
        form = ContactForm()

        # Only show companies belonging to the user's business.
        form.fields["company"].queryset = Company.objects.filter(
            business=membership.business
        )

    return render(
        request,
        "crm/contact_form.html",
        {"form": form},
    )


@login_required
def contact_detail(request, contact_id):
    """Display a contact belonging to the logged-in user's business."""

    membership = Membership.objects.filter(
        user=request.user
    ).select_related("business").first()

    if membership is None:
        return redirect("core:dashboard")

    contact = Contact.objects.filter(
        id=contact_id,
        business=membership.business,
    ).select_related("company").first()

    if contact is None:
        return redirect("crm:contact_list")

    return render(
        request,
        "crm/contact_detail.html",
        {"contact": contact},
    )


@login_required
def contact_edit(request, contact_id):
    """Edit a contact belonging to the logged-in user's business."""

    membership = Membership.objects.filter(
        user=request.user
    ).select_related("business").first()

    if membership is None:
        return redirect("core:dashboard")

    contact = Contact.objects.filter(
        id=contact_id,
        business=membership.business,
    ).select_related("company").first()

    if contact is None:
        return redirect("crm:contact_list")

    if request.method == "POST":
        form = ContactForm(
            request.POST,
            instance=contact,
        )

        # Only allow companies belonging to the user's business.
        form.fields["company"].queryset = Company.objects.filter(
            business=membership.business
        )

        if form.is_valid():
            form.save()

            return redirect(
                "crm:contact_detail",
                contact_id=contact.id,
            )
    else:
        form = ContactForm(instance=contact)

        # Only allow companies belonging to the user's business.
        form.fields["company"].queryset = Company.objects.filter(
            business=membership.business
        )

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

    membership = Membership.objects.filter(
        user=request.user
    ).select_related("business").first()

    if membership is None:
        return redirect("core:dashboard")

    contact = Contact.objects.filter(
        id=contact_id,
        business=membership.business,
    ).first()

    if contact is None:
        return redirect("crm:contact_list")

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

    memberships = Membership.objects.filter(
        user=request.user
    ).select_related("business")

    deals = Deal.objects.filter(
        business__in=memberships.values("business")
    ).select_related("company", "contact")

    return render(
        request,
        "crm/deal_list.html",
        {"deals": deals},
    )


@login_required
def deal_create(request):
    """Create a new deal for the logged-in user's business."""

    membership = Membership.objects.filter(
        user=request.user
    ).select_related("business").first()

    if membership is None:
        return redirect("core:dashboard")

    if request.method == "POST":
        form = DealForm(request.POST)

        # Only show companies belonging to the user's business.
        form.fields["company"].queryset = Company.objects.filter(
            business=membership.business
        )

        # Only show contacts belonging to the user's business.
        form.fields["contact"].queryset = Contact.objects.filter(
            business=membership.business
        )

        if form.is_valid():
            deal = form.save(commit=False)
            deal.business = membership.business
            deal.save()

            return redirect("crm:deal_list")
    else:
        form = DealForm()

        # Only show companies belonging to the user's business.
        form.fields["company"].queryset = Company.objects.filter(
            business=membership.business
        )

        # Only show contacts belonging to the user's business.
        form.fields["contact"].queryset = Contact.objects.filter(
            business=membership.business
        )

    return render(
        request,
        "crm/deal_form.html",
        {"form": form},
    )


@login_required
def deal_detail(request, deal_id):
    """Display a deal belonging to the logged-in user's business."""

    membership = Membership.objects.filter(
        user=request.user
    ).select_related("business").first()

    if membership is None:
        return redirect("core:dashboard")

    deal = Deal.objects.filter(
        id=deal_id,
        business=membership.business,
    ).select_related("company", "contact").first()

    if deal is None:
        return redirect("crm:deal_list")

    return render(
        request,
        "crm/deal_detail.html",
        {"deal": deal},
    )


@login_required
def deal_edit(request, deal_id):
    """Edit a deal belonging to the logged-in user's business."""

    membership = Membership.objects.filter(
        user=request.user
    ).select_related("business").first()

    if membership is None:
        return redirect("core:dashboard")

    deal = Deal.objects.filter(
        id=deal_id,
        business=membership.business,
    ).select_related("company", "contact").first()

    if deal is None:
        return redirect("crm:deal_list")

    if request.method == "POST":
        form = DealForm(
            request.POST,
            instance=deal,
        )

        # Only allow companies belonging to the user's business.
        form.fields["company"].queryset = Company.objects.filter(
            business=membership.business
        )

        # Only allow contacts belonging to the user's business.
        form.fields["contact"].queryset = Contact.objects.filter(
            business=membership.business
        )

        if form.is_valid():
            form.save()

            return redirect(
                "crm:deal_detail",
                deal_id=deal.id,
            )
    else:
        form = DealForm(instance=deal)

        # Only allow companies belonging to the user's business.
        form.fields["company"].queryset = Company.objects.filter(
            business=membership.business
        )

        # Only allow contacts belonging to the user's business.
        form.fields["contact"].queryset = Contact.objects.filter(
            business=membership.business
        )

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

    membership = Membership.objects.filter(
        user=request.user
    ).select_related("business").first()

    if membership is None:
        return redirect("core:dashboard")

    deal = Deal.objects.filter(
        id=deal_id,
        business=membership.business,
    ).first()

    if deal is None:
        return redirect("crm:deal_list")

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

    memberships = Membership.objects.filter(
        user=request.user
    ).select_related("business")

    tasks = Task.objects.filter(
        business__in=memberships.values("business")
    ).select_related("company", "contact", "deal")

    return render(
        request,
        "crm/task_list.html",
        {"tasks": tasks},
    )


@login_required
def task_create(request):
    """Create a new task for the logged-in user's business."""

    membership = Membership.objects.filter(
        user=request.user
    ).select_related("business").first()

    if membership is None:
        return redirect("core:dashboard")

    if request.method == "POST":
        form = TaskForm(request.POST)

        # Only show companies belonging to the user's business.
        form.fields["company"].queryset = Company.objects.filter(
            business=membership.business
        )

        # Only show contacts belonging to the user's business.
        form.fields["contact"].queryset = Contact.objects.filter(
            business=membership.business
        )

        # Only show deals belonging to the user's business.
        form.fields["deal"].queryset = Deal.objects.filter(
            business=membership.business
        )

        if form.is_valid():
            task = form.save(commit=False)
            task.business = membership.business
            task.save()

            return redirect("crm:task_list")

    else:
        form = TaskForm()

        # Only show companies belonging to the user's business.
        form.fields["company"].queryset = Company.objects.filter(
            business=membership.business
        )

        # Only show contacts belonging to the user's business.
        form.fields["contact"].queryset = Contact.objects.filter(
            business=membership.business
        )

        # Only show deals belonging to the user's business.
        form.fields["deal"].queryset = Deal.objects.filter(
            business=membership.business
        )

    return render(
        request,
        "crm/task_form.html",
        {"form": form},
    )


@login_required
def task_detail(request, task_id):
    """Display a task belonging to the logged-in user's business."""

    membership = Membership.objects.filter(
        user=request.user
    ).select_related("business").first()

    if membership is None:
        return redirect("core:dashboard")

    task = Task.objects.filter(
        id=task_id,
        business=membership.business,
    ).select_related("company", "contact", "deal").first()

    if task is None:
        return redirect("crm:task_list")

    return render(
        request,
        "crm/task_detail.html",
        {"task": task},
    )


@login_required
def task_edit(request, task_id):
    """Edit a task belonging to the logged-in user's business."""

    membership = Membership.objects.filter(
        user=request.user
    ).select_related("business").first()

    if membership is None:
        return redirect("core:dashboard")

    task = Task.objects.filter(
        id=task_id,
        business=membership.business,
    ).select_related("company", "contact", "deal").first()

    if task is None:
        return redirect("crm:task_list")

    if request.method == "POST":
        form = TaskForm(
            request.POST,
            instance=task,
        )

        # Only allow records belonging to the user's business.
        form.fields["company"].queryset = Company.objects.filter(
            business=membership.business
        )

        form.fields["contact"].queryset = Contact.objects.filter(
            business=membership.business
        )

        form.fields["deal"].queryset = Deal.objects.filter(
            business=membership.business
        )

        if form.is_valid():
            form.save()

            return redirect(
                "crm:task_detail",
                task_id=task.id,
            )

    else:
        form = TaskForm(instance=task)

        # Only allow records belonging to the user's business.
        form.fields["company"].queryset = Company.objects.filter(
            business=membership.business
        )

        form.fields["contact"].queryset = Contact.objects.filter(
            business=membership.business
        )

        form.fields["deal"].queryset = Deal.objects.filter(
            business=membership.business
        )

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

    membership = Membership.objects.filter(
        user=request.user
    ).select_related("business").first()

    if membership is None:
        return redirect("core:dashboard")

    task = Task.objects.filter(
        id=task_id,
        business=membership.business,
    ).first()

    if task is None:
        return redirect("crm:task_list")

    if request.method == "POST":
        task.delete()

        return redirect("crm:task_list")

    return render(
        request,
        "crm/task_confirm_delete.html",
        {"task": task},
    )