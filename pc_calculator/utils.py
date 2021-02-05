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

def handle_upload(request, course_code, semester_pk, csvFile, user, updated=False):
    success = False
    course = get_object_or_404(Course, code=course_code)
    semester = get_object_or_404(Semester, pk=semester_pk)

    if not updated:
        program_outcome_file = ProgramOutcomeFile.objects.create(pc_file=csvFile, user=user, semester=semester, course=course)
    else:
        program_outcome_file = ProgramOutcomeFile.objects.get(user=user, semester=semester, course=course)
    
    with program_outcome_file.pc_file.open(mode='rb') as csv_file:
        contents_byte_str = csv_file.read()
        result = str(CnM.from_bytes(contents_byte_str, cp_isolation=['cp1254', 'utf_8']).best().first()).strip()

    # with open(program_outcome_file.pc_file.path, newline='', encoding=result['encoding']) as csv_file:
        dialect = csv.Sniffer().sniff(result[:1024] or result, delimiters=[',', ';'])
        # csv_file.seek(0)
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
                        success = False
                        return success

                    program_outcome_result = ProgramOutcomeResult.objects.filter(
                        student=student,
                        course=course,
                        program_outcome=program_outcome,
                        semester=semester).first()

                    sat_input_value = 1 if row[po_idx + 2] == "1" or row[po_idx + 2] == "M" else 0

                    if program_outcome_result:
                        program_outcome_result.satisfaction = sat_input_value
                        program_outcome_result.save()
                    else:
                        ProgramOutcomeResult.objects.create(
                            student=student,
                            course=course,
                            program_outcome=program_outcome,
                            semester=semester,
                            satisfaction=sat_input_value)
                else:
                    success = True
    return success

def export(request):
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="report.csv"'

    # with open("/tmp/csv_file.csv", "w") as tmp_csv_file:
    target_file = response

    writer = csv.writer(target_file)
    writer.writerow(["student_id", "name"] + [po.code for po in ProgramOutcome.objects.all()])

    records = list()
    for student in Student.objects.all():
        poas = list()
        for po in ProgramOutcome.objects.all():
            por = ProgramOutcomeResult.objects.filter(
                student=student,
                program_outcome=po).aggregate(Avg("satisfaction"))
            if por["satisfaction__avg"] is not None:
                poas.append(round(por["satisfaction__avg"]))
            else:
                poas.append('NA')

        records.append([student.no, student.name] + poas)

    writer.writerows(records)

    return response

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
