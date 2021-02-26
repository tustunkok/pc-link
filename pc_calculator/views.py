from django.shortcuts import render, get_object_or_404
from django.contrib import messages
from django.views import generic
from django.urls import reverse_lazy
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core import mail

from rest_framework import mixins
from rest_framework import generics
from rest_framework import permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from django_filters.views import FilterView

from pc_calculator.models import *
from pc_calculator.serializers import *
from pc_calculator.filters import *
from pc_calculator.forms import *
from pc_calculator.utils import *
from django.conf import settings

import pandas as pd
import datetime
import logging
import csv
import io

logger = logging.getLogger('pc_link_custom_logger')

class ProgramOutcomeResultList(generics.ListAPIView):
    queryset = ProgramOutcomeResult.objects.all()
    serializer_class = ProgramOutcomeResultSerializer
    permission_classes = [IsAuthenticated]


class StudentList(generics.ListAPIView):
    queryset = Student.objects.all()
    serializer_class = StudentSerializer
    permission_classes = [IsAuthenticated]


class ProgramOutcomeList(generics.ListAPIView):
    queryset = ProgramOutcome.objects.all()
    serializer_class = ProgramOutcomeSerializer
    permission_classes = [IsAuthenticated]

#############################################################

class ProgramOutcomeFileListView(LoginRequiredMixin, generic.ListView):
    model = ProgramOutcomeFile
    template_name = 'pc_calculator/manage.html'
    paginate_by = 10

    def get_queryset(self):
        if not self.request.user.is_superuser:
            return ProgramOutcomeFile.objects.filter(user=self.request.user).order_by('-date_uploaded')
        return ProgramOutcomeFile.objects.order_by('-date_uploaded')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['semesters'] = Semester.objects.all()
        return context


class ProgramOutcomeFileUpdateView(LoginRequiredMixin, generic.UpdateView):
    model = ProgramOutcomeFile
    fields = ['semester', 'course', 'pc_file']
    template_name = 'pc_calculator/update.html'
    success_url = reverse_lazy('pc-calc:manage')

    def form_valid(self, form):
        semester = form.cleaned_data['semester']
        course = form.cleaned_data['course']
        pc_file = form.cleaned_data['pc_file']
        old_name = self.object.pc_file.name
        
        response = super().form_valid(form)

        os.remove(os.path.join(os.path.dirname(self.object.pc_file.path), old_name))

        upload_result = handle_upload(self.request, course.code, semester.id, pc_file, self.object)

        if upload_result[0]:
            messages.success(self.request, 'Program Outcome file is successfuly updated.')
        else:
            messages.warning(self.request, 'No student from the department exists in the uploaded file.')

        return response


class ProgramOutcomeFileDeleteView(LoginRequiredMixin, generic.DeleteView):
    model = ProgramOutcomeFile
    success_url = reverse_lazy('pc-calc:manage')
    template_name = 'pc_calculator/confirm_delete.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        self.object = self.get_object()
        context['por_objects'] = ProgramOutcomeResult.objects.filter(semester=self.object.semester, course=self.object.course)
        return context

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()

        po_results = ProgramOutcomeResult.objects.filter(semester=self.object.semester, course=self.object.course)
        if os.path.exists(os.path.join(settings.MEDIA_ROOT, str(self.object.pc_file))):
            os.remove(os.path.join(settings.MEDIA_ROOT, str(self.object.pc_file)))
        po_results.delete()

        return super().delete(request, *args, **kwargs)


class ProgramOutcomeFileDeleteOnlyFileView(LoginRequiredMixin, generic.DeleteView):
    model = ProgramOutcomeFile
    success_url = reverse_lazy('pc-calc:manage')
    template_name = 'pc_calculator/confirm_delete.html'

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()

        if os.path.exists(os.path.join(settings.MEDIA_ROOT, str(self.object.pc_file))):
            os.remove(os.path.join(settings.MEDIA_ROOT, str(self.object.pc_file)))

        return super().delete(request, *args, **kwargs)


class ReportFilterView(LoginRequiredMixin, FilterView):
    model = ProgramOutcomeResult
    template_name = 'pc_calculator/report.html'
    filterset_class = ProgramOutcomeResultFilter
    paginate_by = 30

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        resultant_queryset = context['page_obj'].object_list

        students = Student.objects.filter(id__in=set(x[0] for x in resultant_queryset.values_list('student')))
        pos = ProgramOutcome.objects.filter(id__in=set(x[0] for x in resultant_queryset.values_list('program_outcome')))

        context['pos'] = pos
        context['students'] = list()

        for student in students:
            poas = list()
            for po in pos:
                por = ProgramOutcomeResult.objects.filter(
                    student=student,
                    program_outcome=po
                )
                total_number_of_courses = len(po.course_set.all())

                if len(por) == 0:
                    poas.append('NA')
                else:
                    satisfied_pors = por.filter(satisfaction=1)
                    if len(satisfied_pors) >= round(total_number_of_courses / 2):
                        poas.append(1)
                    else:
                        poas.append(0)

            context['students'].append({
                'name': student.name,
                'poas': poas
            })

        return context


def help(request):
    return render(request, 'pc_calculator/help.html')


@login_required
def upload_program_outcome_file(request):
    form = ProgramOutcomeForm(request.POST or None, request.FILES or None)

    if form.is_valid():
        logger.info(f'PO file upload requested by {request.user}.')
        course_code = form.cleaned_data['course']
        semester_pk = form.cleaned_data['semester']
        csvFile = form.cleaned_data['outcome_file']

        upload_result = handle_upload(request, course_code, semester_pk, csvFile)

        if upload_result[0]:
            messages.success(request, f'Program Outcome file is successfuly uploaded. A submission report has been emailed to {request.user.email}.')
            mail.send_mail(
                f'[PÇ-Link]:  Program Outcome Upload for {course_code}',
f'''
The following file has been SUBMITTED.
======================================================================
Uploaded By: {request.user}
File Name: {csvFile}
Number of Processed Students: {upload_result[1]}
Date Submitted: {datetime.datetime.now().strftime("%d/%b/%Y %H:%M:%S")}
======================================================================
''',
                'tolgaustunkok@hotmail.com',
                [request.user.email],
                fail_silently=False
            )
            logger.info(f'[User: {request.user}] - An email has been sent to {request.user.email}.')
        else:
            messages.warning(request, 'No student from the department exists in the uploaded file.')
    
    return render(request, 'pc_calculator/upload.html', { 'form': form })


@login_required
def export(request):
    logger.info(f'Export requested by {request.user}.')
    file_type = request.POST['exp_type']

    tuples = list()
    for po in ProgramOutcome.objects.all():
        tuples += [(po.code, course.code) for course in po.course_set.all()] + [(po.code, 'AVG')]
    index = pd.MultiIndex.from_tuples(tuples)

    report_df = pd.DataFrame(index=Student.objects.values_list('no', 'name'), columns=index)

    records = list()
    for student in Student.objects.filter(graduated_on__isnull=True):
        poas = list()
        for po in ProgramOutcome.objects.all():
            por = ProgramOutcomeResult.objects.filter(
                student=student,
                program_outcome=po
            )

            for pr in por:
                report_df.loc[student.no, (po.code, pr.course.code)] = pr.satisfaction

            total_number_of_courses = len(po.course_set.all())

            if len(por) == 0:
                poas.append('NA')
                report_df.loc[student.no, (po.code, 'AVG')] = 'NA'
            elif len(por) < (total_number_of_courses / 2):
                poas.append('I')
                report_df.loc[student.no, (po.code, 'AVG')] = 'I'
            else:
                satisfied_pors = por.filter(satisfaction=1)
                if len(satisfied_pors) >= round(total_number_of_courses / 2):
                    poas.append(1)
                    report_df.loc[student.no, (po.code, 'AVG')] = '1'
                else:
                    poas.append(0)
                    report_df.loc[student.no, (po.code, 'AVG')] = '0'

        records.append([student.no, student.name] + poas)
    
    csv_report_df = pd.DataFrame(records, columns=["student_id", "name"] + [po.code for po in ProgramOutcome.objects.all()])

    if file_type == 'xlsx':
        xlsx_buffer = io.BytesIO()
        with pd.ExcelWriter(xlsx_buffer) as xlwriter:
            report_df.to_excel(xlwriter)
        xlsx_buffer.seek(0)
        response = HttpResponse(xlsx_buffer.read(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response["Content-Disposition"] = 'attachment; filename="report.xlsx"'
    elif file_type == 'csv':
        csv_buffer = io.StringIO()
        csv_report_df.to_csv(csv_buffer, index=False)
        csv_buffer.seek(0)
        response = HttpResponse(csv_buffer.read(), content_type = 'text/csv')
        response["Content-Disposition"] = 'attachment; filename="report.csv"'

    return response


@login_required
def course_report(request):
    logger.info(f'The list of not uploaded courses is requested by {request.user}.')
    semester_id = request.POST['semester']
    semester = get_object_or_404(Semester, pk=semester_id)
    uploaded_courses_set = set([course_id['course'] for course_id in ProgramOutcomeResult.objects.filter(semester=semester).values('course')])

    return render(request, 'pc_calculator/upload_status.html', {'semester': semester, 'courses': Course.objects.all(), 'ucourses_ids': uploaded_courses_set})


@login_required
def populate_students(request):
    if request.method == 'POST':
        stu_bulk_form = StudentBulkUpload(request.POST, request.FILES)

        if stu_bulk_form.is_valid():
            students_df = pd.read_csv(stu_bulk_form.cleaned_data['students_csv_file'])
            students_df.fillna(value={'transfer_student': False, 'double_major_student': False}, inplace=True)

            print(students_df.tail(10))

            for idx, row in students_df.iterrows():
                Student.objects.update_or_create(
                    no=row['student_id'],
                    defaults={
                        'name': row['name'],
                        'transfer_student': row['transfer_student'],
                        'double_major_student': row['double_major_student'],
                        'graduated_on': None if pd.isna(row['graduated_on']) else datetime.datetime.strptime(row['graduated_on'], "%d/%m/%Y")
                    }
                )

            messages.success(request, 'Update successful.')
        else:
            messages.error(request, f'Update does not successful: {stu_bulk_form.non_field_errors()}')
        
        return redirect('profile')

        # with open("migration_files/cmpe-students.csv", "r") as csv_file:
        #     file_iterable = iter(csv_file)
        #     next(file_iterable)

        #     instances = [Student(
        #         no=row[0],
        #         name=row[1],
        #         transfer_student=bool(int(row[2])),
        #         double_major_student=bool(int(row[3])),
        #         graduated_on=datetime.datetime.strptime(row[4], "%d/%m/%Y") if row[4] != '' else None
        #     ) for row in csv.reader(file_iterable)]
        # Student.objects.bulk_create(instances)
        # return redirect('/admin/pc_calculator/student/')
