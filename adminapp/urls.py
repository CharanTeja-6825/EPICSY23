from django import urls
from django.urls import path
from . import views

urlpatterns = [
    path('', views.homepage, name='homepage'),
    path('studentdetails/',views.studentdetails,name='studentdetails'),
    #path('uploadbyBatch/', views.upload_students, name='uploadstudents')
]