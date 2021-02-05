from django import forms

from pc_calculator.models import *

def get_semesters():
    return [(semester.pk, f"{semester.year_interval} {semester.period_name}") for semester in Semester.objects.filter(active=True)]

def get_courses():
    return [(course.code, f"{course.code} - {course.name}") for course in Course.objects.order_by("code")]

class ProgramOutcomeForm(forms.Form):
    course = forms.ChoiceField(choices=get_courses, label="Select a course:")
    semester = forms.ChoiceField(choices=get_semesters, label="Select a semester:")
    outcome_file = forms.FileField(label="Upload the PÇ File:")

class ProgramOutcomeFileForm(forms.ModelForm):
    class Meta:
        model = ProgramOutcomeFile
        fields = ['semester', 'pc_file']