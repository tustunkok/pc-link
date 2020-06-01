from django.contrib import admin
from .models import (
    Student,
    Course,
    CourseOutcome,
    CourseOutcomeResult,
    Department,
    Semester
)

# Register your models here.
admin.site.register(Semester)
admin.site.register(Department)
admin.site.register(Student)
admin.site.register(Course)
admin.site.register(CourseOutcome)
admin.site.register(CourseOutcomeResult)