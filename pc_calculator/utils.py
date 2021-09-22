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

import csv
import logging
import pandas as pd

from pc_calculator.models import *
from django.shortcuts import get_object_or_404, redirect

logger = logging.getLogger('pc_link_custom_logger')

def force_decode(string, codecs=['utf8', 'cp1254', 'cp1252']):
    for i in codecs:
        try:
            string.decode(i)
            return i
        except UnicodeDecodeError:
            pass
    
    return None


def handle_upload(request, course_code, semester_pk, csvFile, program_outcome_file=None):
    success = False
    num_of_students = 0
    course = get_object_or_404(Course, code=course_code)
    semester = get_object_or_404(Semester, pk=semester_pk)

    if program_outcome_file is None :
        program_outcome_file = ProgramOutcomeFile.objects.create(pc_file=csvFile, user=request.user, semester=semester, course=course)
        logger.debug(f'[User: {request.user}] - New ProgramOutcomeFile record created with details {program_outcome_file}.')
    else:
        logger.debug(f'[User: {request.user}] - Using existing ProgramOutcomeFile record with details {program_outcome_file}.')
    
    with program_outcome_file.pc_file.open(mode='rb') as csv_file:
        contents_byte_str = csv_file.read()
        enc = force_decode(contents_byte_str)

    result_df = pd.read_csv(program_outcome_file.pc_file.path, sep=None, engine='python', encoding=enc)
    
    for idx, row in result_df.iterrows():
        try:
            if row.iloc[2:].str.contains('U').any():
                num_of_students += 1
                continue
        except:
            pass

        student = Student.objects.filter(no=row['student_id']).first()

        if student is not None:
            for po_idx, po in enumerate(set(result_df.columns[2:])):
                program_outcome = get_object_or_404(ProgramOutcome, code=po.strip())
                
                program_outcome_result = ProgramOutcomeResult.objects.filter(
                    student=student,
                    course=course,
                    program_outcome=program_outcome,
                    semester=semester
                ).first()

                sat_input_value = 1 if str(row.iloc[po_idx + 2]) == "1" or str(row.iloc[po_idx + 2]) == "M" else 0

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


def calculate_avgs(row):
    for idx in set(list(zip(*row.index))[0]):
        if row[idx].isna().sum() == len(row[idx]):
            row[idx, f"{idx} AVG"] = 'NA'
        elif (row[idx].isna().sum() - 1) <= len(row[idx]) / 2:
            row[idx, f"{idx} AVG"] = 0 if row[idx].mean() < 0.5 else 1
        else:
            row[idx, f"{idx} AVG"] = 'IN'
    return row


def calculate_unsats(row):
    for idx in set(list(zip(*row.index))[0]):
        row[idx, f"{idx} #UNSAT"] = (row[idx] == 0).sum()
    return row


def export_work(semesters):    
    logger.debug(f'Exporting for semesters: {semesters}')

    tuples = list()
    for po in ProgramOutcome.objects.all():
        tuples += [(po.code, course.code) for course in po.course_set.all()] + [(po.code, f'{po.code} AVG'), (po.code, f'{po.code} #UNSAT')]
    columns = pd.MultiIndex.from_tuples(tuples)

    report_df = pd.DataFrame(index=map(list, zip(*list(Student.objects.filter(graduated_on__isnull=True).values_list('no', 'name')) + [('Analysis', 'Total Number of Assessed Students'), ('Analysis', 'Number of Successful Students'), ('Analysis', 'Successful Student Percantage'), ('Analysis', 'Unsuccessful Student Percantage')])), columns=columns)

    for por in ProgramOutcomeResult.objects.filter(semester__in=semesters, student__graduated_on__isnull=True).order_by('semester__period_order_value'):
        report_df.loc[por.student.no, (por.program_outcome.code, por.course.code)] = por.satisfaction

    report_df.iloc[-4, :] = report_df.iloc[:-4, :].apply(lambda x: x.count(), axis=0) # Total Number of Assessed Students
    report_df.iloc[-3, :] = report_df.iloc[:-4, :].apply(lambda x: x.sum(), axis=0) # Number of Successful Students
    report_df.iloc[-2, :] = report_df.iloc[:-4, :].apply(lambda x: x.mean(), axis=0) # Successful Student Percantage
    report_df.iloc[-1, :] = report_df.iloc[:-4, :].apply(lambda x: (x.count() - x.sum()) / x.count() if x.count() > 0 else -1, axis=0) # Unsuccessful Student Percantage
    
    report_df = report_df.apply(calculate_avgs, axis=1)
    report_df = report_df.apply(calculate_unsats, axis=1)

    return report_df
