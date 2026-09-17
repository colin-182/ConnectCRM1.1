from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError, transaction
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme

from crm.models import Business, Invitation, Membership
from crm.tenancy import build_workspace_url, generate_unique_slug, get_business_and_membership

from .forms import RegistrationForm


def _get_invitation(token):
    if not token:
        return None
    invitation = Invitation.objects.filter(token=token).select_related("business").first()
    if invitation is None or invitation.is_accepted or invitation.is_expired:
        return None
    return invitation


def _create_business_for_user(user):
    name = f"{user.username}'s Business"
    slug = generate_unique_slug(name)
    return Business.objects.create(name=name, slug=slug)


def _root_domain_url(request, path):
    """Build an absolute URL on the bare root domain (no business subdomain)."""

    from django.conf import settings

    scheme = "https" if request.is_secure() else "http"
    host = request.get_host()
    port = f":{host.split(':', 1)[1]}" if ":" in host else ""
    return f"{scheme}://{settings.BASE_DOMAIN}{port}{path}"


def register_view(request):
    if request.user.is_authenticated:
        return redirect("core:dashboard")

    invitation_token = request.POST.get("invitation") if request.method == "POST" else request.GET.get("invitation")
    invitation = _get_invitation(invitation_token)
    if invitation_token and invitation is None:
        return render(request, "accounts/register.html", {"form": RegistrationForm(), "invalid_invitation": True})

    if invitation is not None and request.business is not None and invitation.business_id != request.business.id:
        return render(request, "accounts/register.html", {"form": RegistrationForm(), "invalid_invitation": True})

    if invitation is None and request.business is not None:
        messages.info(request, "Create your ConnectCRM account from the main site.")
        return redirect(_root_domain_url(request, reverse("accounts:register")))

    if request.method == "POST":
        form = RegistrationForm(request.POST, invitation_email=invitation.email if invitation else None)
        if form.is_valid():
            try:
                with transaction.atomic():
                    user = form.save()
                    if invitation is not None:
                        locked = Invitation.objects.select_for_update().select_related("business").get(pk=invitation.pk)
                        if locked.is_accepted or locked.is_expired:
                            raise ValueError("Invitation is no longer valid.")
                        Membership.objects.create(user=user, business=locked.business, role=locked.role)
                        locked.accepted_at = timezone.now()
                        locked.save(update_fields=["accepted_at"])
                        business = locked.business
                    else:
                        business = _create_business_for_user(user)
                        Membership.objects.create(user=user, business=business, role=Membership.ADMIN)
            except ValueError:
                form.add_error(None, "This invitation is no longer valid. Please request a new invitation.")
            except IntegrityError:
                form.add_error(None, "Unable to create your account. Please try again.")
            else:
                login(request, user)
                workspace_url = build_workspace_url(request, business)
                if invitation is None:
                    messages.success(
                        request,
                        f"Your workspace is ready at {workspace_url} — bookmark this URL, "
                        "you'll use it to log in from now on.",
                    )
                return redirect("core:dashboard")
    else:
        form = RegistrationForm(invitation_email=invitation.email if invitation else None)
    return render(request, "accounts/register.html", {"form": form, "invitation": invitation})


def login_view(request):
    if request.user.is_authenticated:
        return redirect("core:dashboard")
    next_url = request.GET.get("next") or request.POST.get("next")
    if request.method == "POST":
        user = authenticate(request, username=request.POST.get("username"), password=request.POST.get("password"))
        if user is not None:
        
            if request.business is not None and not Membership.objects.filter(
                user=user, business=request.business
            ).exists():
                return render(
                    request,
                    "accounts/login.html",
                    {
                        "error": "This account doesn't have access to this workspace.",
                        "next": next_url,
                    },
                )
            login(request, user)
            if url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}, require_https=request.is_secure()):
                return redirect(next_url)
            return redirect("core:dashboard")
        return render(request, "accounts/login.html", {"error": "Invalid username or password.", "next": next_url})
    return render(request, "accounts/login.html", {"next": next_url})


@login_required
def profile_view(request):
    membership, _tenant_locked = get_business_and_membership(request)
    workspace_url = build_workspace_url(request, membership.business) if membership else None
    return render(request, "accounts/profile.html", {"membership": membership, "workspace_url": workspace_url})


def logout_view(request):
    logout(request)
    return redirect("core:home")
