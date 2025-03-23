from django.http import HttpResponse, request
from django.shortcuts import render, redirect

from django.db.models import Q
from django.core.paginator import Paginator

#Final Backend

from django.shortcuts import render, redirect
from django.contrib import messages
import csv
from .models import Student


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


        return redirect('studentdetails')

    return render(request, 'adminapp/homepage.html')




from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import render
from .models import Student  # Ensure Student model is imported

def studentdetails(request):
    query = request.GET.get('query', '')  # Use GET for pagination and search together
    students = Student.objects.filter(
        Q(student_id__iexact=query) | Q(name__icontains=query)
    ) if query else Student.objects.none()

    if not students.exists():
        return render(request, 'adminapp/StudentDetails.html', {'error': True})

    student = students.first()  # Display only the first matching student

    # Convert student's course_grades (dictionary) into a list of tuples (course, grade)
    course_list = list(student.course_grades.items())

    paginator = Paginator(course_list, 10)  # Show 10 courses per page
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    return render(request, 'adminapp/StudentDetails.html', {
        'student': student,
        'page_obj': page_obj,
        'query': query  # Pass query to maintain search state
    })
