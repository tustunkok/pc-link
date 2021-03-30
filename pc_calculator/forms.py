"""
PÇ-Link is a report creation software for MÜDEK.
Copyright (C) 2021  Tolga ÜSTÜNKÖK

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published
by the Free Software Foundation, version 3 of the License.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

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
    excempt_students = forms.BooleanField(required=False, label='Upload list of excempt students', help_text='Only check if you upload the list of except students.')


class StudentBulkUploadForm(forms.Form):
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
