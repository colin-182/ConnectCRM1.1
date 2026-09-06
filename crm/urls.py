from django.urls import path

from . import views

app_name = "crm"

urlpatterns = [
    path("companies/", views.company_list, name="company_list"),
    path("companies/add/", views.company_create, name="company_create"),
    path(
        "companies/<int:company_id>/",
        views.company_detail,
        name="company_detail",
    ),
    path(
        "companies/<int:company_id>/edit/",
        views.company_edit,
        name="company_edit",
    ),
    path(
        "companies/<int:company_id>/delete/",
        views.company_delete,
        name="company_delete",
    ),
]