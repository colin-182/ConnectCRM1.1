from django.http import HttpResponse
from django.shortcuts import render


def home(request):
    return HttpResponse("ConnectCRM Home")


def dashboard(request):
    return render(request, "core/dashboard.html")