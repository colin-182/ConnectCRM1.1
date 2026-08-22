from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),

    # Core application
    path("", include("core.urls")),

    # Account and authentication routes
    path("accounts/", include("accounts.urls")),

    # CRM routes
    path("crm/", include("crm.urls")),
]