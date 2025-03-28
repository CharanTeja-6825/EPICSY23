from django.shortcuts import redirect
from django.db import transaction
from django.core.paginator import Paginator
from django.db.models import Q
from django.db import models, connection
from django.apps import apps
import csv
from django.http import HttpResponse
from django.shortcuts import render
from django.contrib import messages

FAILED_GRADES = {"GP", "WH", "DT", "F", "NA"}  # Define failing grades

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

        # Process each student to count failed courses
        for student in students:
            student.failed_courses_count = sum(1 for grade in student.course_grades.values() if grade in FAILED_GRADES)

        paginator = Paginator(students, 10)
        page_number = request.GET.get('page', 1)
        page_obj = paginator.get_page(page_number)

        return render(request, 'adminapp/StudentDetails.html', {'page_obj': page_obj, 'batch': batch})

    return render(request, 'adminapp/StudentDetails.html')




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
        batch = request.POST.get('batch', "").strip().upper()  # Get batch from input field

        if not csv_file or not csv_file.name.endswith('.csv'):
            messages.error(request, "Please upload a valid CSV file")
            return render(request, 'adminapp/homepage.html')

        if not batch.startswith("Y") or len(batch) != 3:  # Validate batch format
            messages.error(request, "Invalid batch format. Use format like Y20, Y21, etc.")
            return render(request, 'adminapp/homepage.html')

        # Read CSV file
        decoded_file = csv_file.read().decode('utf-8').splitlines()
        reader = csv.DictReader(decoded_file)

        headers = reader.fieldnames
        id_column = headers[0]  # First column: student_id
        name_column = headers[1]  # Second column: student name
        course_columns = headers[2:]  # Remaining columns: courses

        # Get or create the corresponding batch model
        StudentModel = get_or_create_model(batch)

        batch_students = []

        for row in reader:
            student_id = row.get(id_column, "").strip()
            name = row.get(name_column, "").strip()

            if not student_id or not name:
                continue

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
                batch_students.append(student)

        # Bulk insert new students into respective batch tables
        if batch_students:
            with transaction.atomic():  # Ensures atomicity
                StudentModel.objects.bulk_create(batch_students, ignore_conflicts=True)

        messages.success(request, f"Student data for {batch} uploaded successfully with updates applied.")
        return redirect('studentdetails')

    return render(request, 'adminapp/homepage.html')


def generate_backlog_report(request):
    if request.method == 'POST':
        batch = request.POST.get('batch', "").strip().upper()

        if not batch.startswith("Y") or len(batch) != 3:  # Validate batch format
            messages.error(request, "Invalid batch format. Use format like Y20, Y21, etc.")
            return render(request, 'adminapp/BacklogReport.html')

        # Get the correct model for the batch
        StudentModel = get_or_create_model(batch)

        # Fetch students with failed courses
        students = StudentModel.objects.all()

        # Prepare data for CSV
        backlog_data = []

        for student in students:
            for course, grade in student.course_grades.items():
                if grade in FAILED_GRADES:
                    backlog_data.append([student.student_id, course, grade])

        if not backlog_data:
            messages.warning(request, "No students with backlogs found.")
            return render(request, 'adminapp/BacklogReport.html')

        # Create CSV response
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename=backlog_report_{batch}.csv'

        writer = csv.writer(response)
        writer.writerow(["Student ID", "Failed Course Code", "Grade"])

        for row in backlog_data:
            writer.writerow(row)

        return response

    return render(request, 'adminapp/BacklogReport.html')
