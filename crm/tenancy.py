from django.db.models import Q
from django.utils.text import slugify

from .models import Business, Membership


def build_workspace_url(request, business):
    """Return the absolute URL of a business's dedicated workspace."""

    scheme = "https" if request.is_secure() else "http"
    host = request.get_host()
    port = ""
    if ":" in host:
        port = f":{host.split(':', 1)[1]}"

    from django.conf import settings

    return f"{scheme}://{business.slug}.{settings.BASE_DOMAIN}{port}/"


def get_business_and_membership(request):
    """Resolve the active (membership, tenant_locked) pair for a request.

    Returns a tuple of (membership, tenant_locked):
      - membership is the caller's Membership for the active business, or
        None if they don't have one.
      - tenant_locked is True when the request arrived on a specific
        business subdomain. Callers MUST treat membership=None as "access
        denied" in that case, rather than falling back to any other
        business the user might belong to.
    """

    tenant = getattr(request, "business", None)
    if tenant is not None:
        membership = (
            Membership.objects.filter(user=request.user, business=tenant)
            .select_related("business")
            .first()
        )
        return membership, True

    membership = (
        Membership.objects.filter(user=request.user)
        .select_related("business")
        .first()
    )
    return membership, False


def generate_unique_slug(name, *, exclude_pk=None):
    """Generate a Business slug from a name, avoiding collisions and
    reserved subdomains (www, admin, static, ...)."""

    from django.conf import settings

    base_slug = slugify(name)[:90] or "business"
    slug = base_slug
    counter = 2

    def taken(candidate):
        if candidate in settings.RESERVED_SUBDOMAINS:
            return True
        qs = Business.objects.filter(slug=candidate)
        if exclude_pk is not None:
            qs = qs.exclude(pk=exclude_pk)
        return qs.exists()

    while taken(slug):
        suffix = f"-{counter}"
        slug = f"{base_slug[:100 - len(suffix)]}{suffix}"
        counter += 1

    return slug


def scope_deals_for_membership(queryset, membership):
    """Restrict a Deal queryset to what this membership may see.

    Admins (sales managers) see every deal for the whole team, with a
    "granular view" filter available in the UI to drill into one team
    member's deals at a time. Everyone else sees only deals assigned to
    them, plus any unassigned deals, so legacy/unowned deals don't just
    disappear for them.
    """

    if membership.role == Membership.ADMIN:
        return queryset
    return queryset.filter(Q(owner=membership.user) | Q(owner__isnull=True))
