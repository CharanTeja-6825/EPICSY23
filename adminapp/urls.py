from django import urls
from django.urls import path
from . import views

urlpatterns = [
    path('', views.homepage, name='homepage'),
    path('studentdetails/',views.studentdetails,name='studentdetails'),
    # path('get_student_info/<str:student_id>/', views.get_student_info, name='get_student_info'),
    # path("upload/", views.upload_csv, name="upload_csv"),
]