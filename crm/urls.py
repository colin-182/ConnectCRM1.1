from django.urls import path

from . import views

app_name = "crm"

urlpatterns = [
    path("companies/", views.company_list, name="company_list"),
    path("companies/add/", views.company_create, name="company_create"),
]