from django.http import HttpResponse, request
from django.shortcuts import render, redirect
import csv
from django.contrib import messages
from django.db import transaction
from django.db.models import Q
from django.core.paginator import Paginator

#Final Backend


def studentdetails(request):
    if request.method == 'POST':
        query = request.POST.get('query', "").strip()

        if not query:
            return render(request, 'adminapp/StudentDetails.html', {'error': True})

        batch_prefix = query[:2]  # Extract batch year from student ID (e.g., "20" from "200123")
        batch = f"Y{batch_prefix}"  # Convert to batch format (e.g., "Y20")

        # Dynamically get the batch-specific student model
        StudentModel = get_or_create_model(batch)

        # Fetch students matching the query in the selected batch
        students = StudentModel.objects.filter(
            Q(student_id__iexact=query) | Q(name__icontains=query)
        ).order_by('student_id')

        if not students.exists():
            return render(request, 'adminapp/StudentDetails.html', {'error': True})

        paginator = Paginator(students, 10)
        page_number = request.GET.get('page', 1)
        page_obj = paginator.get_page(page_number)

        return render(request, 'adminapp/StudentDetails.html', {'page_obj': page_obj, 'batch': batch})

    return render(request, 'adminapp/StudentDetails.html')

from django.db import models, connection
from django.apps import apps

def create_batch_table(batch):
    """Creates a table for the given batch if it does not exist."""
    table_name = f"students_{batch}"

    with connection.cursor() as cursor:
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {table_name} (
                student_id VARCHAR(15) PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                course_grades JSON NOT NULL
            )
        """)

def create_batch_model(batch):
    """Dynamically create a model for a given batch."""
    class Meta:
        db_table = f"students_{batch}"  # Set table name

    attrs = {
        '__module__': __name__,
        'student_id': models.CharField(max_length=15, primary_key=True),
        'name': models.CharField(max_length=100),
        'course_grades': models.JSONField(),
        'Meta': Meta,
    }

    model_name = f"Student{batch}"
    return type(model_name, (models.Model,), attrs)

def get_or_create_model(batch):
    """Retrieve an existing batch model or create a new one dynamically."""
    model_name = f"Student{batch}"

    if model_name in apps.all_models['adminapp']:
        return apps.get_model('adminapp', model_name)

    # Create table if it does not exist
    create_batch_table(batch)

    # Create and register the model
    model = create_batch_model(batch)
    apps.all_models['adminapp'][model_name.lower()] = model
    apps.register_model('adminapp', model)

    return model

def homepage(request):
    if request.method == 'POST':
        csv_file = request.FILES.get('csv_file')
        if not csv_file or not csv_file.name.endswith('.csv'):
            messages.error(request, "Please upload a valid CSV file")
            return render(request, 'adminapp/homepage.html')

        # Read CSV file
        decoded_file = csv_file.read().decode('utf-8').splitlines()
        reader = csv.DictReader(decoded_file)

        headers = reader.fieldnames
        id_column = headers[0]  # First column: student_id
        name_column = headers[1]  # Second column: student name
        course_columns = headers[2:]  # Remaining columns: courses

        batch_students = {}

        for row in reader:
            student_id = row.get(id_column, "").strip()
            name = row.get(name_column, "").strip()

            if not student_id or not name:
                continue

            batch = "Y" + student_id[:2]  # Extract batch from student ID (e.g., "20" → "Y20")

            # Get or create the corresponding batch model
            StudentModel = get_or_create_model(batch)

            # Collect course grades, skipping empty values
            course_grades = {course: row[course].strip() for course in course_columns if row[course].strip()}

            # Check if the student already exists
            existing_student = StudentModel.objects.filter(student_id=student_id).first()

            if existing_student:
                # Update existing student's course grades
                existing_grades = existing_student.course_grades or {}
                existing_grades.update(course_grades)  # Merge new grades with old ones
                existing_student.course_grades = existing_grades
                existing_student.save()
            else:
                # Add new student to batch
                student = StudentModel(
                    student_id=student_id,
                    name=name,
                    course_grades=course_grades
                )
                if batch not in batch_students:
                    batch_students[batch] = []
                batch_students[batch].append(student)

        # Bulk insert new students into respective batch tables
        for batch, students in batch_students.items():
            StudentModel = get_or_create_model(batch)
            with transaction.atomic():  # Ensures atomicity
                StudentModel.objects.bulk_create(students, ignore_conflicts=True)

        messages.success(request, "Student data uploaded successfully with updates applied.")
        return redirect('studentdetails')

    return render(request, 'adminapp/homepage.html')
