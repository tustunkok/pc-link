import os
import csv
import datetime

from pc_calculator.models import *
from django.shortcuts import get_object_or_404, redirect
from django.core.files import File
from django.contrib import messages
from pc_link_rest.settings import BASE_DIR
from django.http import HttpResponse
from django.db.models import Avg
from charset_normalizer import CharsetNormalizerMatches as CnM

def handle_upload(request, course_code, semester_pk, csvFile, user, logger, updated=False):
    success = False
    course = get_object_or_404(Course, code=course_code)
    semester = get_object_or_404(Semester, pk=semester_pk)

    file_type = os.path.splitext(str(csvFile))[1].lower()
    if file_type != '.csv':
        messages.error(request, f"Wrong file type: {file_type}. It should be a CSV file.")
        logger.info(f'File type found to be {file_type} for the uploaded file {csvFile}, it should be CSV.')
        return success

    if not updated:
        program_outcome_file = ProgramOutcomeFile.objects.create(pc_file=csvFile, user=user, semester=semester, course=course)
        logger.debug(f'New ProgramOutcomeFile record created with details {program_outcome_file}.')
    else:
        program_outcome_file = ProgramOutcomeFile.objects.get(user=user, semester=semester, course=course)
        logger.debug(f'Existing ProgramOutcomeFile record is updated with details {program_outcome_file}.')
    
    with program_outcome_file.pc_file.open(mode='rb') as csv_file:
        contents_byte_str = csv_file.read()
        det_result = CnM.from_bytes(contents_byte_str, cp_isolation=['cp1254', 'utf_8']).best().first()
        logger.debug(f'The encoding of uploaded file {program_outcome_file.pc_file} is determined as {det_result.could_be_from_charset[0]}.')

    result = str(det_result).strip()

    dialect = csv.Sniffer().sniff(result[:1024] or result, delimiters=[',', ';'])
    logger.debug(f"The delimiter of uploaded file {program_outcome_file.pc_file} is determined as '{dialect.delimiter}'.")
    result = result.split('\n')

    first_row = True
    for row in csv.reader(result, dialect):
        if first_row:
            first_row = False
            program_outcomes = row[2:]
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
                    logger.info(f"No program outcome found named as {po}.")
                    success = False
                    return success

                program_outcome_result = ProgramOutcomeResult.objects.filter(
                    student=student,
                    course=course,
                    program_outcome=program_outcome,
                    semester=semester).first()

                sat_input_value = 1 if row[po_idx + 2] == "1" or row[po_idx + 2] == "M" else 0

                if program_outcome_result:
                    logger.debug(f'Existing ProgramOutcomeResult record updated. Previously {program_outcome_result.satisfaction}, now {sat_input_value}')
                    program_outcome_result.satisfaction = sat_input_value
                    program_outcome_result.save()
                else:
                    program_outcome_result = ProgramOutcomeResult.objects.create(
                        student=student,
                        course=course,
                        program_outcome=program_outcome,
                        semester=semester,
                        satisfaction=sat_input_value)
                    logger.debug(f'New ProgramOutcomeResult record created for student: {student}, course: {course}, program outcome: {program_outcome}, semester: {semester}, and satisfaction: {sat_input_value}.')
            else:
                success = True
                logger.info(f'ProgramOutcomeResult record for {program_outcome_result} is created or updated successfully.')
        else:
            logger.debug(f'No student found with an id {row[0]}.')
    return success

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
