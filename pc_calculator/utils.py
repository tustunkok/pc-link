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

import os
import io
import csv
import logging
import datetime
import pandas as pd
import numpy as np

from pc_calculator.models import *
from django.shortcuts import get_object_or_404, redirect
from django.core.files import File
from django.contrib import messages
from django.conf import settings
from django.http import HttpResponse

logger = logging.getLogger('pc_link_custom_logger')

def validate_uploaded_file(request, delimiter, file_contents, program_outcome_file):
    failed = False
    logger.debug(f"[User: {request.user}] - Uploaded file contents are started to be validated.")

    try:
        test_df = pd.read_csv(io.StringIO(file_contents), sep=delimiter)
    except pd.errors.ParserError as e:
        logger.error(f'[User: {request.user}] - File cannot be parsed: {e}')
    
    line_analysis_U = test_df.iloc[:, 2:].apply(lambda x: all(x.values == 'U') if 'U' in x.values else True, axis=1)
    line_analysis = test_df.iloc[:, 2:].isin(['U', 'M', '1', '0', 1, 0]).all(axis=1)

    if not test_df.columns[:2].isin(['student_id', 'name']).all():
        messages.error(request, 'The headers of the file should be student_id, name, and PÇ codes.')
        os.remove(os.path.join(settings.MEDIA_ROOT, str(program_outcome_file.pc_file)))
        program_outcome_file.delete()
        failed = True

    if not line_analysis_U.all():
        messages.error(request, f'Line(s) {", ".join((np.nonzero(line_analysis_U.values == False)[0] + 2).astype(str).tolist())} of the uploaded file is wrong.')
        os.remove(os.path.join(settings.MEDIA_ROOT, str(program_outcome_file.pc_file)))
        program_outcome_file.delete()
        failed = True
    
    if not line_analysis.all():
        messages.error(request, f'Wrong input value in line(s) {", ".join((np.nonzero(line_analysis.values == False)[0] + 2).astype(str).tolist())} of the uploaded file.')
        failed = True
    
    return failed


def force_decode(string, codecs=['utf8', 'cp1254', 'cp1252']):
    for i in codecs:
        try:
            return (i, string.decode(i))
        except UnicodeDecodeError:
            pass


def handle_upload(request, course_code, semester_pk, csvFile, program_outcome_file=None):
    success = False
    num_of_students = 0
    course = get_object_or_404(Course, code=course_code)
    semester = get_object_or_404(Semester, pk=semester_pk)

    file_type = os.path.splitext(str(csvFile))[1].lower()
    if file_type != '.csv':
        messages.error(request, f"Wrong file type: {file_type}. It should be a CSV file.")
        logger.error(f'[User: {request.user}] - File type found to be {file_type} for the uploaded file {csvFile}, it should be CSV.')
        return (success, num_of_students)

    if program_outcome_file is None :
        program_outcome_file = ProgramOutcomeFile.objects.create(pc_file=csvFile, user=request.user, semester=semester, course=course)
        logger.debug(f'[User: {request.user}] - New ProgramOutcomeFile record created with details {program_outcome_file}.')
    else:
        logger.debug(f'[User: {request.user}] - Using existing ProgramOutcomeFile record with details {program_outcome_file}.')
    
    with program_outcome_file.pc_file.open(mode='rb') as csv_file:
        contents_byte_str = csv_file.read()
        enc, det_result = force_decode(contents_byte_str)

        if det_result is not None:
            logger.debug(f'[User: {request.user}] - The encoding of uploaded file {program_outcome_file.pc_file} is determined as {enc}.')
        else:
            messages.error(request, f'File encoding cannot be determined. It should be one of {["cp1254", "utf_8", "cp1252"]}')
            logger.error(f'[User: {request.user}] - The encoding of uploaded file cannot be determined.')
            return (success, num_of_students)

    result = str(det_result).strip()

    dialect = csv.Sniffer().sniff(result[:1024] or result, delimiters=[',', ';'])
    logger.debug(f"[User: {request.user}] - The delimiter of uploaded file {program_outcome_file.pc_file} is determined as '{dialect.delimiter}'.")

    if validate_uploaded_file(request, dialect.delimiter, result, program_outcome_file): # if failed
        return (success, num_of_students)
    
    result_df = pd.read_csv(io.StringIO(result), sep=dialect.delimiter)
    file_pos = set(result_df.columns[2:])
    uploaded_course_pos = set([x.code for x in course.program_outcomes.all()])

    if not file_pos == uploaded_course_pos:
        logger.error(f'[User: {request.user}] - The program outcomes in the uploaded file do not match the program outcomes of the registered course for course {course}.')
        messages.error(request, f'The program outcomes in the uploaded file do not match the program outcomes of the registered course for course {course}.')
        os.remove(os.path.join(settings.MEDIA_ROOT, str(program_outcome_file.pc_file)))
        program_outcome_file.delete()
        return (success, num_of_students)
    
    for idx, row in result_df.iterrows():
        try:
            if row.iloc[2:].str.contains('U').any():
                num_of_students += 1
                continue
        except:
            pass

        student = Student.objects.filter(no=row['student_id'], graduated_on__isnull=True).first()

        if student is not None:
            for po_idx, po in enumerate(file_pos):
                try:
                    program_outcome = ProgramOutcome.objects.get(
                        code=po.strip()
                    )
                except:
                    messages.error(request, f"No program outcome found named as {po}.")
                    logger.error(f"[User: {request.user}] - No program outcome found named as {po}.")
                    success = False
                    return (success, num_of_students)
                
                program_outcome_result = ProgramOutcomeResult.objects.filter(
                    student=student,
                    course=course,
                    program_outcome=program_outcome,
                    semester=semester
                ).first()

                sat_input_value = 1 if str(row.iloc[po_idx + 2]) == "1" or str(row.iloc[po_idx + 2]) == "M" else 0
                
                try:
                    ProgramOutcomeResult.objects.exclude(semester=semester).get(course=course, student=student, program_outcome=program_outcome).delete()
                    logger.debug(f'Existing records for semester {semester} are replaced with new ones for student {student}, course {course}, and program outcome {program_outcome}')
                except:
                    pass

                if program_outcome_result:
                    logger.debug(f'[User: {request.user}] - Existing ProgramOutcomeResult record {program_outcome_result} updated. Previously {program_outcome_result.satisfaction}, now {sat_input_value}')
                    program_outcome_result.satisfaction = sat_input_value
                    program_outcome_result.save()
                else:
                    program_outcome_result = ProgramOutcomeResult.objects.create(
                        student=student,
                        course=course,
                        program_outcome=program_outcome,
                        semester=semester,
                        satisfaction=sat_input_value
                    )
                    logger.debug(f'[User: {request.user}] - New ProgramOutcomeResult record created for student: {student}, course: {course}, program outcome: {program_outcome}, semester: {semester}, and satisfaction: {sat_input_value}.')
            else:
                success = True
                logger.info(f'[User: {request.user}] - ProgramOutcomeResult record for {program_outcome_result} is created or updated successfully.')
                num_of_students += 1
        else:
            logger.debug(f'[User: {request.user}] - No student found with an id {row[0]}.')

    return (success, num_of_students)
    

def handle_excempt_students(request, csv_file):
    csv_file_df = pd.read_csv(io.BytesIO(csv_file.read()), sep=None, engine='python')

    if len(csv_file_df.columns) != 4:
        messages.error(request, 'Something is wrong with the uploaded CSV file.')
        return

    for _, row in csv_file_df.iterrows():
        semester_year_interval = row[3].split(' ')[0]
        semester_period_name = row[3].split(' ')[1]

        semester = get_object_or_404(Semester, year_interval=semester_year_interval, period_name=semester_period_name)
        course = get_object_or_404(Course, code=row[2])
        student = get_object_or_404(Student, no=row['student_id'])

        for po in course.program_outcomes.all():
            ProgramOutcomeResult.objects.update_or_create(
                semester=semester,
                course=course,
                student=student,
                program_outcome=po,
                defaults={'satisfaction': 1}
            )
    
    messages.success(request, 'File successfuly uploaded and processed.')


def populate_program_outcomes(request):
    with open("migration_files/program_outcomes.csv", "r") as csv_file:
        file_iterable = iter(csv_file)
        next(file_iterable)

        instances = [ProgramOutcome(
            code=row[0],
            description=row[1]
        ) for row in csv.reader(file_iterable)]
    ProgramOutcome.objects.bulk_create(instances)
    return redirect('/admin/pc_calculator/programoutcome/')

def populate_courses(request):
    with open("migration_files/course-cmpe.csv", "r") as csv_file:
        file_iterable = iter(csv_file)
        next(file_iterable)

        instances = list()
        for row in csv.reader(file_iterable):
            course = Course(code=row[0], name=row[1])
            course.save()
            course.program_outcomes.add(*[ProgramOutcome.objects.get(code=f'PÇ{po}') for po in row[2].split('-')])
    return redirect('/admin/pc_calculator/course/')
