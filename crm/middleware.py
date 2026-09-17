from django.conf import settings
from django.shortcuts import render

from .models import Business


class TenantMiddleware:
    """Attach request.business based on the subdomain of the request.

    - Root domain (BASE_DOMAIN or "www.<BASE_DOMAIN>"), or a host that
      isn't a recognised subdomain at all (e.g. plain "localhost:8000"
      during local development before subdomains are set up): request.business
      is set to None. Views fall back to legacy single-tenant behaviour.
    - A reserved subdomain (www, admin, static, ...): treated the same as
      the root domain.
    - A subdomain that matches a real Business slug: request.business is
      that Business.
    - A subdomain that looks like a workspace but matches no Business:
      the visitor is shown a "workspace not found" page instead of being
      allowed through, so no view ever runs with a half-resolved tenant.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.business = None

        host = request.get_host().split(":")[0].lower()
        base_domain = settings.BASE_DOMAIN.lower()

        subdomain = None
        if host == base_domain or host in ("localhost", "127.0.0.1"):
            subdomain = None
        elif host.endswith(f".{base_domain}"):
            subdomain = host[: -(len(base_domain) + 1)]
        # Any other host (e.g. a custom domain that isn't configured) is
        # treated as the root domain rather than guessed at.

        if subdomain and subdomain not in settings.RESERVED_SUBDOMAINS:
            business = Business.objects.filter(slug=subdomain).first()
            if business is None:
                return render(
                    request,
                    "core/workspace_not_found.html",
                    {"attempted_slug": subdomain, "base_domain": settings.BASE_DOMAIN},
                    status=404,
                )
            request.business = business

        return self.get_response(request)
