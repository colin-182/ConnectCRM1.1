from django.urls import path

from . import views

app_name = "crm"

urlpatterns = [
    path("companies/", views.company_list, name="company_list"),
    path("companies/add/", views.company_create, name="company_create"),
    path("companies/<int:company_id>/", views.company_detail, name="company_detail"),
    path("companies/<int:company_id>/edit/", views.company_edit, name="company_edit"),
    path("companies/<int:company_id>/delete/", views.company_delete, name="company_delete"),
    path("contacts/", views.contact_list, name="contact_list"),
    path("contacts/add/", views.contact_create, name="contact_create"),
    path("contacts/<int:contact_id>/", views.contact_detail, name="contact_detail"),
    path("contacts/<int:contact_id>/edit/", views.contact_edit, name="contact_edit"),
    path("contacts/<int:contact_id>/delete/", views.contact_delete, name="contact_delete"),
    path("deals/", views.deal_list, name="deal_list"),
    path("deals/add/", views.deal_create, name="deal_create"),
    path("deals/<int:deal_id>/", views.deal_detail, name="deal_detail"),
    path("deals/<int:deal_id>/edit/", views.deal_edit, name="deal_edit"),
    path("deals/<int:deal_id>/delete/", views.deal_delete, name="deal_delete"),
    path("tasks/", views.task_list, name="task_list"),
    path("tasks/add/", views.task_create, name="task_create"),
    path("tasks/<int:task_id>/", views.task_detail, name="task_detail"),
    path("tasks/<int:task_id>/edit/", views.task_edit, name="task_edit"),
    path("tasks/<int:task_id>/toggle/", views.task_toggle, name="task_toggle"),
    path("tasks/<int:task_id>/delete/", views.task_delete, name="task_delete"),
    path("search/", views.search, name="search"),
    path("search/suggestions/", views.search_suggestions, name="search_suggestions"),
    path("invitations/add/", views.invitation_create, name="invitation_create"),
    path("invitations/<str:token>/", views.invitation_accept, name="invitation_accept"),
]
