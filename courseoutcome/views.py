import csv
import pandas as pd

from django.shortcuts import render, redirect, reverse, get_object_or_404, get_list_or_404
from django.contrib.auth.decorators import login_required
from django.views.generic.list import ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse, Http404
from django.core.paginator import Paginator
from django.db.models import Avg

from .models import (
    Student,
    Department,
    Semester,
    Course,
    CourseOutcome,
    CourseOutcomeResult
)

from .forms import CourseOutcomeForm

def index(request):
    return render(request, "courseoutcome/index.html", {})

class CourseOutcomeAverageListView(LoginRequiredMixin, ListView):
    template_name = "courseoutcome/report.html"
    paginate_by = 10

    def get_queryset(self):
        try:
            semester = get_object_or_404(Semester, pk=self.kwargs["semester_id"])
            department = get_object_or_404(Department, code=self.kwargs["department"])
        except:
            return []
        
        context_students = Student.objects.filter(department=department)
        context_cors = CourseOutcomeResult.objects.filter(semester=semester)

        try:
            self.course_outcome = get_object_or_404(CourseOutcome, code=self.kwargs["course_outcome"])
            context_cors = context_cors.filter(course_outcome=self.course_outcome)
        except:
            # TODO: This code block must be logged.
            pass
        
        try:
            context_students = get_list_or_404(Student, no=self.kwargs["student"])
        except:
            # TODO: This code block must be logged.
            pass
        

        records = list()
        for student in context_students:
            coas = list()
            for co in [self.course_outcome] if hasattr(self, "course_outcome") else CourseOutcome.objects.order_by("order"):
                coa = context_cors.filter(
                    student=student,
                    course_outcome=co).aggregate(Avg("satisfaction"))
                if coa["satisfaction__avg"] is not None:
                    coas.append(round(coa["satisfaction__avg"]))
                else:
                    coas.append(0)
            records.append([student.no, student.name, student.department.code, coas])
        
        return records

    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if hasattr(self, "course_outcome"):
            context["chosen_cos"] = [self.course_outcome]
        else:
            context["chosen_cos"] = CourseOutcome.objects.order_by("order")
        
        context["semesters"] = Semester.objects.all()
        context["departments"] = Department.objects.all()
        context["outcomes"] = CourseOutcome.objects.order_by("order")
        context["students"] = Student.objects.all()
        return context

def generate_query(request):
    resulting_page_str = reverse("courseoutcome:report")

    if request.POST.get("department_code") and request.POST.get("semester_pk"):
        resulting_page_str += f"{request.POST.get('department_code')}/{request.POST.get('semester_pk')}/"
        if request.POST.get("co_code"):
            resulting_page_str += f"{request.POST.get('co_code')}/"
            if request.POST.get("student_no"):
                resulting_page_str += f"{request.POST.get('student_no')}/"
        elif request.POST.get("student_no"):
                resulting_page_str += f"{request.POST.get('student_no')}/"
    
    return redirect(resulting_page_str)

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
    else:
        raise Http404("Page does not exist.")

    with open("/tmp/csv_file.csv", "w") as tmp_csv_file:
        target_file = response if export_type == "csv" else tmp_csv_file

        writer = csv.writer(target_file)
        writer.writerow(["student_id", "name", "department"] + [co.code for co in CourseOutcome.objects.order_by("order").all()])

        records = list()
        for student in Student.objects.all():
            coas = list()
            for co in CourseOutcome.objects.order_by("order").all():
                coa = CourseOutcomeResult.objects.filter(
                    student=student,
                    course_outcome=co).aggregate(Avg("satisfaction"))
                if coa["satisfaction__avg"] is not None:
                    coas.append(round(coa["satisfaction__avg"]))
                else:
                    coas.append(0)

            records.append([student.no, student.name, student.department.code] + coas)

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

                    course_outcome_result = CourseOutcomeResult.objects.filter(
                        student=student,
                        course=course,
                        course_outcome=course_outcome,
                        semester=semester).first()

                    sat_input_value = 1 if row[co_idx + 2] == "1" or row[co_idx + 2] == "M" else 0

                    if course_outcome_result:
                        course_outcome_result.satisfaction = sat_input_value
                        course_outcome_result.save()
                    else:
                        CourseOutcomeResult.objects.create(
                            student=student,
                            course=course,
                            course_outcome=course_outcome,
                            semester=semester,
                            satisfaction=sat_input_value)

def populate(request):
    Department.objects.bulk_create([
        Department(code="CMPE", name="Computer Engineering"),
        Department(code="SE", name="Software Engineering")
    ])

    Semester.objects.bulk_create([
        Semester(year_interval="2019-2020", period_name="Fall"),
        Semester(year_interval="2019-2020", period_name="Spring")
    ])

    with open("migration_files/courseoutcome_student.csv", "r") as csv_file:
        instances = [Student(no=row[1], name=row[2], graduated_on=row[3] if row[3] != "" else None, department=Department.objects.get(pk=int(row[4])), double_major_student=bool(int(row[5])), vertical_transfer=bool(int(row[6]))) for row in csv.reader(csv_file)]

    Student.objects.bulk_create(instances)

    with open("migration_files/cmpe-students.csv", "r") as csv_file:
        instances = [Student(no=row[0], name=row[1], department=Department.objects.get(code="CMPE")) for row in csv.reader(csv_file)]

    Student.objects.bulk_create(instances)

    with open("migration_files/courseoutcome_course.csv", "r") as csv_file:
        instances = [Course(code=row[1], name=row[2]) for row in csv.reader(csv_file)]

    Course.objects.bulk_create(instances)

    with open("migration_files/courseoutcome_courseoutcome.csv", "r") as csv_file:
        instances = [CourseOutcome(code=row[1], order=int(row[2])) for row in csv.reader(csv_file)]

    CourseOutcome.objects.bulk_create(instances)

    return redirect("/courseoutcome/")