from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .forms import CompanyForm
from .models import Company, Membership


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
    """Display a company belonging to the logged-in user's business."""

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

    return render(
        request,
        "crm/company_detail.html",
        {"company": company},
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
        form = CompanyForm(request.POST, instance=company)

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