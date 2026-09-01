from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm
from django.db import transaction
from django.shortcuts import redirect, render

from crm.models import Business, Membership


def register_view(request):
    """Create a new user, business and admin membership."""

    if request.user.is_authenticated:
        return redirect("core:dashboard")

    if request.method == "POST":
        form = UserCreationForm(request.POST)

        if form.is_valid():
            with transaction.atomic():
                user = form.save()

                business = Business.objects.create(
                    name=f"{user.username}'s Business"
                )

                Membership.objects.create(
                    user=user,
                    business=business,
                    role=Membership.ADMIN,
                )

            login(request, user)

            return redirect("core:dashboard")
    else:
        form = UserCreationForm()

    return render(
        request,
        "accounts/register.html",
        {"form": form},
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
    return redirect("core:landing")