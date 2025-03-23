from django.db import models

# Create your models here.
from django.db import models

class StudentGrade(models.Model):
    student_id = models.CharField(max_length=20)
    course_name = models.CharField(max_length=100)
    grade = models.CharField(max_length=5)

    def __str__(self):
        return f"{self.student_id} - {self.course_name}: {self.grade}"
