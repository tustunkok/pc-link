import os
import io
import csv
import datetime
import pandas as pd
import numpy as np

from pc_calculator.models import *
from django.shortcuts import get_object_or_404, redirect
from django.core.files import File
from django.contrib import messages
from pc_link_rest.settings import BASE_DIR, MEDIA_ROOT
from django.http import HttpResponse
from django.db.models import Avg
from charset_normalizer import CharsetNormalizerMatches as CnM

def validate_uploaded_file(logger, request, delimiter, file_contents):
    failed = False
    logger.debug(f"[User: {request.user}] - Uploaded file contents are started to be validated.")

    try:
        test_df = pd.read_csv(io.StringIO(file_contents), sep=delimiter)
    except pd.errors.ParserError as e:
        logger.error(f'[User: {request.user}] - File cannot be parsed: {e}')
    
    line_analysis_U = test_df.iloc[:, 2:].apply(lambda x: all(x.values == 'U') if 'U' in x.values else True, axis=1)
    line_analysis = test_df.iloc[:, 2:].isin(['U', 'M', '1', '0', 1, 0]).all(axis=1)
    print()

    if not line_analysis_U.all():
        messages.error(request, f'Line(s) {", ".join((np.nonzero(line_analysis_U.values == False)[0] + 2).astype(str).tolist())} of the uploaded file is wrong.')
        failed = True
    
    if not line_analysis.all():
        messages.error(request, f'Wrong input value in line(s) {", ".join((np.nonzero(line_analysis.values == False)[0] + 2).astype(str).tolist())} of the uploaded file.')
        failed = True
    
    return failed

def handle_upload(request, course_code, semester_pk, csvFile, user, logger, updated=False):
    success = False
    num_of_students = 0
    course = get_object_or_404(Course, code=course_code)
    semester = get_object_or_404(Semester, pk=semester_pk)

    file_type = os.path.splitext(str(csvFile))[1].lower()
    if file_type != '.csv':
        messages.error(request, f"Wrong file type: {file_type}. It should be a CSV file.")
        logger.error(f'[User: {request.user}] - File type found to be {file_type} for the uploaded file {csvFile}, it should be CSV.')
        return (success, num_of_students)

    if not updated:
        program_outcome_file = ProgramOutcomeFile.objects.create(pc_file=csvFile, user=user, semester=semester, course=course)
        logger.debug(f'[User: {request.user}] - New ProgramOutcomeFile record created with details {program_outcome_file}.')
    else:
        program_outcome_file = ProgramOutcomeFile.objects.get(user=user, semester=semester, course=course)
        logger.debug(f'[User: {request.user}] - Existing ProgramOutcomeFile record is updated with details {program_outcome_file}.')
    
    with program_outcome_file.pc_file.open(mode='rb') as csv_file:
        contents_byte_str = csv_file.read()
        det_result = CnM.from_bytes(contents_byte_str, cp_isolation=['cp1254', 'utf_8', 'cp1252']).best().first()

        if det_result.could_be_from_charset:
            logger.debug(f'[User: {request.user}] - The encoding of uploaded file {program_outcome_file.pc_file} is determined as {det_result.could_be_from_charset[0]}.')
        else:
            messages.error(request, f'File encoding cannot be determined. It should be one of {["cp1254", "utf_8", "cp1252"]}')
            logger.error(f'[User: {request.user}] - The encoding of uploaded file cannot be determined.')
            return (success, num_of_students)

    result = str(det_result).strip()

    dialect = csv.Sniffer().sniff(result[:1024] or result, delimiters=[',', ';'])
    logger.debug(f"[User: {request.user}] - The delimiter of uploaded file {program_outcome_file.pc_file} is determined as '{dialect.delimiter}'.")

    if validate_uploaded_file(logger, request, dialect.delimiter, result): # if failed
        return (success, num_of_students)

    result = result.split('\n')

    first_row = True
    for row in csv.reader(result, dialect):
        if first_row:
            first_row = False
            program_outcomes = row[2:]

            if not all(x.code in program_outcomes for x in course.program_outcomes.all()):
                logger.error(f'[User: {request.user}] - The program outcomes in the uploaded file do not match the program outcomes of the registered course for course {course}.')
                messages.error(request, f'The program outcomes in the uploaded file do not match the program outcomes of the registered course for course {course}.')
                os.remove(os.path.join(MEDIA_ROOT, str(program_outcome_file.pc_file)))
                program_outcome_file.delete()
                return (success, num_of_students)

            continue

        student = Student.objects.filter(no=row[0]).first()
        
        if student is not None:
            for po_idx, po in enumerate(program_outcomes):
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
                    semester=semester).first()

                if row[po_idx + 2].upper() != 'U':
                    sat_input_value = 1 if row[po_idx + 2] == "1" or row[po_idx + 2] == "M" else 0

                    if program_outcome_result:
                        logger.debug(f'[User: {request.user}] - Existing ProgramOutcomeResult record updated. Previously {program_outcome_result.satisfaction}, now {sat_input_value}')
                        program_outcome_result.satisfaction = sat_input_value
                        program_outcome_result.save()
                    else:
                        program_outcome_result = ProgramOutcomeResult.objects.create(
                            student=student,
                            course=course,
                            program_outcome=program_outcome,
                            semester=semester,
                            satisfaction=sat_input_value)
                        logger.debug(f'[User: {request.user}] - New ProgramOutcomeResult record created for student: {student}, course: {course}, program outcome: {program_outcome}, semester: {semester}, and satisfaction: {sat_input_value}.')
                else:
                    logger.debug(f'[User: {request.user}] - New ProgramOutcomeResult record does not created for student: {student}, course: {course}, semester: {semester}.')
                    break
            else:
                success = True
                logger.info(f'[User: {request.user}] - ProgramOutcomeResult record for {program_outcome_result} is created or updated successfully.')
                num_of_students += 1
        else:
            logger.debug(f'[User: {request.user}] - No student found with an id {row[0]}.')
    return (success, num_of_students)

def populate_students(request):
    with open("migration_files/cmpe-students.csv", "r") as csv_file:
        file_iterable = iter(csv_file)
        next(file_iterable)

        instances = [Student(
            no=row[0],
            name=row[1],
            transfer_student=bool(int(row[2])),
            double_major_student=bool(int(row[3])),
            graduated_on=datetime.datetime.strptime(row[4], "%d/%m/%Y") if row[4] != '' else None
        ) for row in csv.reader(file_iterable)]
    Student.objects.bulk_create(instances)
    return redirect('/admin/pc_calculator/student/')

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
