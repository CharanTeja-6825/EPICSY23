from django.http import HttpResponse, request
from django.shortcuts import render

# Create your views here.
# def homepage(request):
#     return render(request, 'adminapp/homepage.html')
#
# def studentdetails(request):
#     return render(request, 'adminapp/StudentDetails.html')

from django.shortcuts import render
from django.http import HttpResponse
from django.contrib import messages
from django.db.models import Q
from django.core.paginator import Paginator
import csv
from .models import Student

#Final Backend
def homepage(request):
    if request.method == 'POST':
        csv_file = request.FILES.get('csv_file')
        if not csv_file or not csv_file.name.endswith('.csv'):
            messages.error(request, "Please upload a valid CSV file")
            return render(request, 'adminapp/homepage.html')

        Student.objects.all().delete()  # Clear previous data

        decoded_file = csv_file.read().decode('utf-8').splitlines()
        reader = csv.DictReader(decoded_file)

        # Identify dynamic column names
        headers = reader.fieldnames
        id_column = headers[0]  # Assume first column is the student ID
        name_column = headers[1]  # Assume second column is the student name
        course_columns = headers[2:]  # Remaining columns are courses

        batch = []
        batch_size = 500

        for row in reader:
            student_id = row.get(id_column, "").strip()
            name = row.get(name_column, "").strip()

            if not student_id or not name:
                continue  # Skip empty records

            # Store all remaining columns dynamically
            course_grades = {course: row[course] for course in course_columns if row[course].strip()}

            student = Student(
                student_id=student_id,
                name=name,
                course_grades=course_grades
            )
            batch.append(student)

            if len(batch) >= batch_size:
                Student.objects.bulk_create(batch)
                batch = []

        if batch:
            Student.objects.bulk_create(batch)

        messages.success(request, f"Uploaded {Student.objects.count()} students successfully!")
        return render(request, 'adminapp/homepage.html')

    return render(request, 'adminapp/homepage.html')

def studentdetails(request):
    if request.method == 'POST':
        query = request.POST.get('query')
        students = Student.objects.filter(
            Q(student_id__iexact=query) | Q(name__icontains=query)
        ).order_by('student_id')

        if not students.exists():
            return render(request, 'adminapp/StudentDetails.html', {'error': True})

        paginator = Paginator(students, 10)
        page_number = request.GET.get('page', 1)
        page_obj = paginator.get_page(page_number)
        return render(request, 'adminapp/StudentDetails.html', {'page_obj': page_obj})
    return render(request, 'adminapp/StudentDetails.html')