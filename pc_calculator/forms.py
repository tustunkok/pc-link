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
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from django.shortcuts import get_object_or_404
import pandas as pd
import numpy as np
import os
import io
import logging
from .utils import force_decode

from pc_calculator.models import *

logger = logging.getLogger('pc_link_custom_logger')

def get_semesters():
    return [(semester.pk, f"{semester.year_interval} {semester.period_name}") for semester in Semester.objects.filter(active=True).order_by('-period_order_value')]

def get_all_semesters():
    return [(semester.pk, f"{semester.year_interval} {semester.period_name}") for semester in Semester.objects.all().order_by('period_order_value')]

def get_courses():
    return [(course.code, f"{course.code} - {course.name}") for course in Course.objects.order_by("code")]


class ProgramOutcomeForm(forms.Form):
    course = forms.ChoiceField(choices=get_courses, label="Select a course:")
    semester = forms.ChoiceField(choices=get_semesters, label="Select a semester:")
    outcome_file = forms.FileField(label="Upload the PÇ File:")

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

    def clean_outcome_file(self):
        data = self.cleaned_data['outcome_file']

        # Check for file type. Give an error if file type is not CSV.
        file_type = os.path.splitext(str(data))[1].lower()
        if file_type != '.csv':
            logger.info(f'[User: {self.user}] - File type found to be {file_type} for the uploaded file {data}, it should be CSV.')
            raise ValidationError(
                'File type should be CSV. Not %(file_type)s',
                params={'file_type': file_type},
                code='invalid'
            )
        
        # Check for encoding of the file is supported.
        contents_byte_str = data.read()
        enc = force_decode(contents_byte_str)
        data.seek(0)
    
        if enc is None:
            logger.info(f'[User: {self.user}] - The encoding of uploaded file cannot be determined.')
            raise ValidationError(
                'The file encoding should be one of UTF-8, Windows 1254, or Windows 1252.',
                code='invalid'
            )
        
        # Check if the file can be parsed by pandas.
        try:
            self.data_df = pd.read_csv(io.BytesIO(contents_byte_str), sep=None, engine='python', encoding=enc)
        except Exception as e:
            logger.info(f'[User: {self.user}] - File cannot be parsed: {e}')
            raise ValidationError(
                'File cannot be parsed by pandas: %(error)s',
                params={'error': e},
                code='invalid'
            )
        
        # Check if the column names of the first two columns are correct.
        if not self.data_df.columns[:2].isin(['student_id', 'name']).all():
            logger.info('The headers of the file should be student_id, name, and PÇ codes.')
            raise ValidationError(
                'The headers of the file should be student_id, name, and exact PÇ codes.',
                code='invalid'
            )
        
        # Check if the lines containing Us are correct.
        correct_U_lines = self.data_df.iloc[:, 2:].apply(lambda x: np.all(x.values == 'U') if x.isin(['U']).any() else True, axis=1)
        if not correct_U_lines.all():
            wrong_lines = ", ".join((np.nonzero(correct_U_lines.values == False)[0] + 2).astype(str).tolist())
            logger.info(f'Line(s) {wrong_lines} of the uploaded file is wrong.')
            raise ValidationError(
                'The usage of U is wrong in lines %(wrong_lines)s.',
                params={'wrong_lines': wrong_lines},
                code='invalid'
            )

        # Check if the values in the lines are expected or not.
        correct_lines = self.data_df.iloc[:, 2:].isin(['U', 'M', '1', '0', 1, 0]).all(axis=1)
        if not correct_lines.all():
            wrong_lines = ", ".join((np.nonzero(correct_lines.values == False)[0] + 2).astype(str).tolist())
            logger.info(f'Wrong input value in line(s) {wrong_lines} of the uploaded file.')
            raise ValidationError(
                'Following lines have unexpected characters: %(wrong_lines)s.',
                params={'wrong_lines': wrong_lines},
                code='invalid'
            )
        
        return data
    
    def clean(self):
        cleaned_data = super().clean()

        # Check if the program outcomes of the uploaded file matches with the actual program outcomes of the file.
        if hasattr(self, 'data_df'):
            course = get_object_or_404(Course, code=cleaned_data.get('course'))
            file_pos = set(self.data_df.columns[2:])
            uploaded_course_pos = set([x.code for x in course.program_outcomes.all()])
            if file_pos != uploaded_course_pos:
                logger.info(f'[User: {self.user}] - The program outcomes in the uploaded file do not match the program outcomes of the registered course for course {course}.')
                raise ValidationError(
                    'The program outcomes in the uploaded file do not match the program outcomes of the registered course for course %(course)s.',
                    params={'course': course},
                    code='invalid'
                )

        return cleaned_data


class StudentBulkUploadForm(forms.Form):
    students_csv_file = forms.FileField(label='Upload Updated Students CSV File:')

    def clean_students_csv_file(self):
        data = self.cleaned_data.get('students_csv_file')
        uploaded_file_ext = os.path.splitext(data.name)[1]

        if uploaded_file_ext != '.csv':
            raise ValidationError(
                'The file extension does not indicate a CSV file.',
                code='invalid'
            )
        
        return data


class ExportReportForm(forms.Form):
    export_type = forms.ChoiceField(choices=[('xlsx', 'Microsoft Excel File (.xlsx)'), ('csv', 'Comma Separated Values File (.csv)')], label='Export type:')
    semesters = forms.MultipleChoiceField(choices=get_all_semesters, label='Choose the semesters that you want to take into account:')


class ExportDiffReportForm(forms.Form):
    export_type = forms.ChoiceField(choices=[('xlsx', 'Microsoft Excel File (.xlsx)'), ('csv', 'Comma Separated Values File (.csv)')], label='Export type:')
    first_semesters = forms.MultipleChoiceField(choices=get_all_semesters, label='Choose the first group of semesters that you want to compare:')
    second_semesters = forms.MultipleChoiceField(choices=get_all_semesters, label='Choose the second group of semesters that you want to compare:')


class RestoreBackupForm(forms.Form):
    snapshot_file = forms.FileField(label="Snapshot File:", validators=[FileExtensionValidator(allowed_extensions=['zip'])])
