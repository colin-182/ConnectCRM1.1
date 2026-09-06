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
    path("contacts/", views.contact_list, name="contact_list"),
path("contacts/add/", views.contact_create, name="contact_create"),
path(
    "contacts/<int:contact_id>/",
    views.contact_detail,
    name="contact_detail",
),
path(
    "contacts/<int:contact_id>/edit/",
    views.contact_edit,
    name="contact_edit",
),
path(
    "contacts/<int:contact_id>/delete/",
    views.contact_delete,
    name="contact_delete",
),
]