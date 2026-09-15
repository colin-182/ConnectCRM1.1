from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.db import IntegrityError, transaction
from django.shortcuts import redirect, render
from django.utils import timezone

from crm.models import Invitation, Membership

from .forms import RegistrationForm


def register_view(request):
    """Create a new user account, optionally through an invitation."""

    if request.user.is_authenticated:
        return redirect("core:dashboard")

    invitation_token = request.GET.get("invitation")

    if request.method == "POST":
        invitation_token = request.POST.get("invitation")

    invitation = None

    if invitation_token:
        invitation = (
            Invitation.objects.filter(
                token=invitation_token,
            )
            .select_related("business")
            .first()
        )

        if (
            invitation is None
            or invitation.is_accepted
            or invitation.is_expired
        ):
            return render(
                request,
                "accounts/register.html",
                {
                    "form": RegistrationForm(),
                    "invalid_invitation": True,
                },
            )

    if request.method == "POST":
        form = RegistrationForm(request.POST)

        if invitation is not None:
            form.fields["email"].initial = invitation.email

        if form.is_valid():
            try:
                with transaction.atomic():
                    user = form.save()

                    if invitation is not None:
                        Membership.objects.create(
                            user=user,
                            business=invitation.business,
                            role=invitation.role,
                        )

                        invitation.accepted_at = timezone.now()
                        invitation.save(
                            update_fields=["accepted_at"]
                        )
                    else:
                        from crm.models import Business

                        business = Business.objects.create(
                            name=f"{user.username}'s Business"
                        )

                        Membership.objects.create(
                            user=user,
                            business=business,
                            role=Membership.ADMIN,
                        )

            except IntegrityError:
                form.add_error(
                    None,
                    "Unable to create your account. Please try again.",
                )
            else:
                login(request, user)
                return redirect("core:dashboard")
    else:
        if invitation is not None:
            form = RegistrationForm(
                initial={
                    "email": invitation.email,
                }
            )
        else:
            form = RegistrationForm()

    return render(
        request,
        "accounts/register.html",
        {
            "form": form,
            "invitation": invitation,
        },
    )


def login_view(request):
    """Authenticate an existing user and start their session."""

    if request.user.is_authenticated:
        return redirect("core:dashboard")

    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(
            request,
            username=username,
            password=password,
        )

        if user is not None:
            login(request, user)
            return redirect("core:dashboard")

        return render(
            request,
            "accounts/login.html",
            {
                "error": "Invalid username or password.",
            },
        )

    return render(request, "accounts/login.html")


def logout_view(request):
    """Log the current user out and return to the landing page."""

    logout(request)
    return redirect("core:home")