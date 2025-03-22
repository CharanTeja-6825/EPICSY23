from django.http import HttpResponse, request
from django.shortcuts import render

# Create your views here.
def homepage(request):
    return render(request, 'adminapp/homepage.html')
