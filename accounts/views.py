from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError, transaction
from django.shortcuts import redirect, render
from django.utils import timezone
from django.utils.text import slugify

from .forms import RegistrationForm
from crm.models import Business, Invitation, Membership


def _generate_business_slug(username):
    """Generate a unique workspace slug from a username."""

    base_slug = slugify(username) or "business"
    slug = base_slug
    counter = 2

    while Business.objects.filter(slug=slug).exists():
        slug = f"{base_slug}-{counter}"
        counter += 1

    return slug


def register_view(request):
    """Create a new business or accept an invitation during registration."""

    if request.user.is_authenticated:
        return redirect("core:dashboard")

    invitation_token = request.POST.get(
        "invitation"
    ) or request.GET.get(
        "invitation"
    )

    invitation = None
    invitation_error = None

    if invitation_token:
        invitation = Invitation.objects.filter(
            token=invitation_token,
        ).select_related("business").first()

        if invitation is None:
            invitation_error = (
                "This invitation is invalid or no longer available."
            )
        elif invitation.is_accepted:
            invitation_error = (
                "This invitation has already been accepted."
            )
            invitation = None
        elif invitation.is_expired:
            invitation_error = (
                "This invitation has expired."
            )
            invitation = None

    if request.method == "POST":
        form = RegistrationForm(request.POST)

        if invitation_error:
            form.add_error(
                None,
                invitation_error,
            )

        if invitation is not None:
            submitted_email = request.POST.get(
                "email",
                "",
            ).strip().lower()

            if submitted_email != invitation.email.lower():
                form.add_error(
                    "email",
                    (
                        "Please use the email address that received "
                        "this invitation."
                    ),
                )

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
                        business = Business.objects.create(
                            name=f"{user.username}'s Business",
                            slug=_generate_business_slug(
                                user.username
                            ),
                        )

                        Membership.objects.create(
                            user=user,
                            business=business,
                            role=Membership.ADMIN,
                        )

            except IntegrityError:
                form.add_error(
                    "username",
                    "That username is already taken. Please choose another.",
                )
            else:
                login(request, user)
                return redirect("core:dashboard")

    else:
        form = RegistrationForm()

    return render(
        request,
        "accounts/register.html",
        {
            "form": form,
            "invitation": invitation,
            "invitation_token": invitation_token,
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