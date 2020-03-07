import csv
import pandas as pd

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.generic import ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.core.paginator import Paginator

from .models import (
    Student,
    Department,
    Semester,
    Course,
    CourseOutcomeResult,
    CourseOutcome,
    CourseOutcomeAverage
)

from .forms import CourseOutcomeForm

@login_required
def report(request):
    std_id = request.GET.get('student_no', False)
    co_code = request.GET.get("co_code", False)
    dpt_code = request.GET.get("department_code", False)
    smster_pk = request.GET.get("semester_pk", False)

    if std_id == "all" and co_code == "all":
        query = CourseOutcomeAverage.objects.all()
    elif std_id == "all" and co_code != "all":
        query = CourseOutcomeAverage.objects.filter(course_outcome__code=co_code)
    elif std_id != "all" and co_code == "all":
        query = CourseOutcomeAverage.objects.filter(student__no=std_id)
    elif std_id != "all" and co_code != "all":
        query = CourseOutcomeAverage.objects.filter(student__no=std_id, course_outcome__code=co_code)
    
    query_dict = dict()

    for item in query:
        query_dict[item.student.no] = list()

    for item in query:
        query_dict[item.student.no].append(item)

    context = dict()
    context["outcomes"] = CourseOutcome.objects.order_by("order").all()
    context["students"] = Student.objects.order_by("name").all()
    context["departments"] = Department.objects.all()
    context["semesters"] = Semester.objects.all()
    context["chosen_cos"] = CourseOutcome.objects.all() if co_code == "all" else CourseOutcome.objects.filter(code=co_code)

    paginator = Paginator(list(query_dict.values()), 12)

    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    if std_id: context["is_paginated"] = True

    context["page_obj"] = page_obj
    context["co_results"] = paginator.page(page_number).object_list

    return render(request, "courseoutcome/report.html", context=context)

@login_required
def upload(request):
    form = CourseOutcomeForm(request.POST or None, request.FILES or None)

    if form.is_valid():
        course_code = form.cleaned_data["course"]
        semester_pk = form.cleaned_data["semester"]
        csvFile = form.cleaned_data["outcome_file"]

        handle_upload(course_code, semester_pk, csvFile)

    context = {
        "form": form
    }

    return render(request, "courseoutcome/upload.html", context)

@login_required
def export(request):
    export_type = request.POST.get("exp_type", False)

    if export_type == "csv":
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="report.csv"'
    elif export_type == "excel":
        response = HttpResponse(content_type="application/ms-excel")
        response["Content-Disposition"] = 'attachment; filename="report.xlsx"'

    with open("/tmp/csv_file.csv", "w") as tmp_csv_file:
        target_file = response if export_type == "csv" else tmp_csv_file

        writer = csv.writer(target_file)
        writer.writerow(["student_id", "name"] + [co.code for co in CourseOutcome.objects.order_by("order").all()])

        records = list()
        for student in Student.objects.all():
            coas = list()
            for co in CourseOutcome.objects.order_by("order").all():
                coa = CourseOutcomeAverage.objects.filter(student=student, course_outcome=co).first()
                if coa is not None:
                    coas.append(int(coa.overall_satisfaction))
                else:
                    coas.append("0")

            records.append([student.no, student.name] + coas)

        writer.writerows(records)

    if export_type == "excel":
        excel_df = pd.read_csv("/tmp/csv_file.csv")
        excel_df.to_excel(response)

    return response

def handle_upload(course_code, semester_pk, csvFile):
    course = get_object_or_404(Course, code=course_code)
    semester = get_object_or_404(Semester, pk=semester_pk)

    with open('/tmp/django_tmp_file.csv', 'wb') as destination:
        for chunk in csvFile.chunks():
            destination.write(chunk)

    with open("/tmp/django_tmp_file.csv", "r") as csv_file:
        first_row = True
        for row in csv.reader(csv_file):
            if first_row:
                first_row = False
                course_outcomes = row[2:]
                continue

            student = Student.objects.filter(no=row[0]).first()
            
            if student is not None:
                for co_idx, co in enumerate(course_outcomes):
                    course_outcome = CourseOutcome.objects.get(code=co)

                    course_outcome_result = CourseOutcomeResult.objects.filter(student=student, course=course, course_outcome=course_outcome, semester=semester).first()
                    if course_outcome_result:
                        course_outcome_result.satisfaction = row[co_idx + 2]
                        course_outcome_result.save()
                    else:
                        CourseOutcomeResult.objects.create(student=student, course=course, course_outcome=course_outcome, semester=semester, satisfaction=row[co_idx + 2])
                    
                    cor_student_records_all_courses = CourseOutcomeResult.objects.filter(student=student, course_outcome=course_outcome, semester=semester)
                    satisfactions = [cor.satisfaction for cor in cor_student_records_all_courses if cor.satisfaction == "1" or cor.satisfaction == "0" or cor.satisfaction == "M"]
                    ones_count = satisfactions.count("1") + satisfactions.count("M")
                    zeros_count = satisfactions.count("0")
                    satisfaction_res = int(ones_count >= zeros_count) if ones_count > 0 else 0

                    course_outcome_average = CourseOutcomeAverage.objects.filter(student=student, course_outcome=course_outcome, semester=semester).first()
                    if course_outcome_average:
                        course_outcome_average.overall_satisfaction = satisfaction_res
                        course_outcome_average.save()
                    else:
                        CourseOutcomeAverage.objects.create(student=student, course_outcome=course_outcome, semester=semester, overall_satisfaction=satisfaction_res)

def bulk_insert_students(request):
    csv_location = "/home/tustunkok/Documents/Atilim University/MÜDEK/MUDEK Management/courseoutcome_student.csv"

    with open(csv_location, "r") as csv_file:
        instances = [Student(no=row[1], name=row[2], graduated_on=row[3] if row[3] != "" else None, department=Department.objects.get(pk=int(row[4])), double_major_student=bool(int(row[5])), vertical_transfer=bool(int(row[6]))) for row in csv.reader(csv_file)]

    Student.objects.bulk_create(instances)

    return redirect("/admin/")

def bulk_insert_courses(request):
    csv_location = "/home/tustunkok/Documents/Atilim University/MÜDEK/MUDEK Management/courseoutcome_course.csv"

    with open(csv_location, "r") as csv_file:
        instances = [Course(code=row[1], name=row[2]) for row in csv.reader(csv_file)]

    Course.objects.bulk_create(instances)

    return redirect("/admin/")

def bulk_insert_courseoutcomes(request):
    csv_location = "/home/tustunkok/Documents/Atilim University/MÜDEK/MUDEK Management/courseoutcome_courseoutcome.csv"

    with open(csv_location, "r") as csv_file:
        instances = [CourseOutcome(code=row[1], order=int(row[2])) for row in csv.reader(csv_file)]

    CourseOutcome.objects.bulk_create(instances)

    return redirect("/admin/")

def recalculate_everything(request):
    CourseOutcomeAverage.objects.all().delete()

    for student in Student.objects.all():
        for course_outcome in CourseOutcome.objects.all():
            cors = CourseOutcomeResult.objects.filter(student=student, course_outcome=course_outcome)

            satisfactions = [cor.satisfaction for cor in cors if cor.satisfaction == "1" or cor.satisfaction == "0" or cor.satisfaction == "M"]
            ones_count = satisfactions.count("1") + satisfactions.count("M")
            zeros_count = satisfactions.count("0")
            overall_satisfaction = int(ones_count >= zeros_count) if ones_count > 0 else 0
                
            CourseOutcomeAverage.objects.create(student=student, course_outcome=course_outcome, semester=Semester.objects.all().first(), overall_satisfaction=overall_satisfaction)
    
    return redirect("/courseoutcome/")