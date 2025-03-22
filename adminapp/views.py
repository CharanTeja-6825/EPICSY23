from django.http import HttpResponse, request
from django.shortcuts import render

# Create your views here.
def homepage(request):
    return render(request, 'adminapp/homepage.html')

def studentdetails(request):
    return render(request, 'adminapp/StudentDetails.html')
