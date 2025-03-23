from django.http import HttpResponse, request
from django.shortcuts import render

# Create your views here.
def homepage(request):
    return render(request, 'adminapp/homepage.html')

def studentdetails(request):
    return render(request, 'adminapp/StudentDetails.html')


import pandas as pd
from django.shortcuts import render, redirect
from django.core.files.storage import FileSystemStorage
from .models import StudentGrade
from django.http import JsonResponse

def upload_csv(request):
    if request.method == 'POST' and request.FILES['csv_file']:
        csv_file = request.FILES['csv_file']
        fs = FileSystemStorage()
        file_path = fs.save(csv_file.name, csv_file)
        file_url = fs.path(file_path)

        # Read CSV file
        df = pd.read_csv(file_url)

        # Drop existing table data
        StudentGrade.objects.all().delete()

        # Insert new data
        records = [
            StudentGrade(
                student_id=row['student_id'],
                course_name=row['course_name'],
                grade=row['grade']
            ) for _, row in df.iterrows()
        ]
        StudentGrade.objects.bulk_create(records)

        return JsonResponse({'message': 'CSV uploaded and data saved successfully!'})

    return render(request, 'adminapp/homepage.html')



from django.shortcuts import render
from django.http import JsonResponse
from .models import StudentGrade

def get_student_info(request, student_id):
    records = StudentGrade.objects.filter(student_id=student_id)

    if not records.exists():
        return JsonResponse({'error': 'Student not found'}, status=404)

    # Assuming additional student details are fetched elsewhere
    student_data = {
        'name': "R Charan Teja",  # Replace with actual logic to fetch name
        'reg_number': student_id,
        'course_branch': "B.Tech - Computer Science Engineering",
        'courses_registered': 65,
        'courses_detained': 5,
        'grades': [
            {'course_code': record.course_name, 'grade': record.grade}
            for record in records
        ]
    }

    return JsonResponse(student_data)

