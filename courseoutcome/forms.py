from django import forms

from .models import Course, Semester

class CourseOutcomeForm(forms.Form):
    initial_courses = [(course.code, f"{course.code} - {course.name}") for course in Course.objects.all()]
    initial_semesters = [(semester.pk, f"{semester.year_interval} {semester.period_name}") for semester in Semester.objects.all()]
    
    course = forms.ChoiceField(choices=initial_courses, label="Select a course:")
    semester = forms.ChoiceField(choices=initial_semesters, label="Select a semester:")
    outcome_file = forms.FileField(label="Upload the PÇ File:")
