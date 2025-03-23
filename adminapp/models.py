from django.db import models

# Create your models here.
from django.db import models

class Student(models.Model):
    student_id = models.CharField(max_length=15, primary_key=True)
    name = models.CharField(max_length=100, db_index=True)
    course_grades = models.JSONField()  # Stores all course details dynamically

    def __str__(self):
        return f"{self.name} ({self.student_id})"
