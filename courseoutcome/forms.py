from django import forms

from .models import Course, Semester

def get_semesters():
    return [(semester.pk, f"{semester.year_interval} {semester.period_name}") for semester in Semester.objects.all()]

def get_courses():
    return [(course.code, f"{course.code} - {course.name}") for course in Course.objects.all()]

class CourseOutcomeForm(forms.Form):
    course = forms.ChoiceField(choices=get_courses, label="Select a course:")
    semester = forms.ChoiceField(choices=get_semesters, label="Select a semester:")
    outcome_file = forms.FileField(label="Upload the PÇ File:")