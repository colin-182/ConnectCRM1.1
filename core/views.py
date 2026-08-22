from django.http import HttpResponse


def home(request):
    return HttpResponse("ConnectCRM Home")


def dashboard(request):
    return HttpResponse("ConnectCRM Dashboard")