from django import forms
import os
from django.core.exceptions import ValidationError

from pc_calculator.models import *

def get_semesters():
    return [(semester.pk, f"{semester.year_interval} {semester.period_name}") for semester in Semester.objects.filter(active=True)]

def get_all_semesters():
    return [(semester.pk, f"{semester.year_interval} {semester.period_name}") for semester in Semester.objects.all()]

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


class StudentBulkUpload(forms.Form):
    students_csv_file = forms.FileField(label='Upload Updated Students CSV File:')

    def clean(self):
        cleaned_data = super().clean()
        uploaded_file_ext = os.path.splitext(cleaned_data.get('students_csv_file').name)[1]

        if uploaded_file_ext != '.csv':
            raise ValidationError(
                'The file extension does not indicate a CSV file.'
            )


class ExportReportForm(forms.Form):
    export_type = forms.ChoiceField(choices=[('xlsx', 'Microsoft Excel File (.xlsx)'), ('csv', 'Comma Separated Values File (.csv)')], label='Export type:')
    semesters = forms.MultipleChoiceField(choices=get_all_semesters, label='Choose the semesters that you want to take into account:')
