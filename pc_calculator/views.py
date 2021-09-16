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

from django.shortcuts import render, get_object_or_404
from django.contrib import messages
from django.views import generic
from django.urls import reverse_lazy
from django.http import HttpResponse, FileResponse
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core import mail
from django.conf import settings
from django.core.management import call_command
from django.db.models import Count, Max
from maintenance_mode.core import set_maintenance_mode

from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from pc_calculator.models import *
from pc_calculator.serializers import *
from pc_calculator.forms import *
from pc_calculator.utils import *

from itertools import chain
import pandas as pd
import datetime
import logging
import shutil
import io
import os

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


@login_required
def report_view(request):
    export_report_form = ExportReportForm()
    export_diff_report_form = ExportDiffReportForm()
    return render(request, 'pc_calculator/report.html', {'export_form': export_report_form, 'export_diff_form': export_diff_report_form})


def help(request):
    return render(request, 'pc_calculator/help.html')


@login_required
def upload_program_outcome_file(request):
    form = ProgramOutcomeForm(request.POST or None, request.FILES or None, user=request.user)

    if form.is_valid():
        logger.info(f'PO file upload requested by {request.user}.')
        course_code = form.cleaned_data['course']
        semester_pk = form.cleaned_data['semester']
        csvFile = form.cleaned_data['outcome_file']

        upload_result = handle_upload(request, course_code, semester_pk, csvFile)

        if upload_result[0]:
            messages.success(request, f'Program Outcome file is successfuly uploaded. A submission report has been emailed to {request.user.email}.')
            if settings.DEBUG == False:
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
                    'pc-link@atilim.edu.tr',
                    [request.user.email],
                    fail_silently=False
                )
            logger.info(f'[User: {request.user}] - An email has been sent to {request.user.email}.')
        else:
            messages.warning(request, 'No student from the department exists in the uploaded file.')
    
    return render(request, 'pc_calculator/upload.html', { 'form': form, 'active_semester_count': Semester.objects.filter(active=True).count() })


@login_required
@staff_member_required
def handle_excempt_students(request):
    if request.method == 'POST':
        form = StudentBulkUploadForm(request.POST, request.FILES)

        if form.is_valid():
            csv_file = form.cleaned_data['students_csv_file']
            csv_file_df = pd.read_csv(io.BytesIO(csv_file.read()), sep=None, engine='python')

            if len(csv_file_df.columns) != 4:
                messages.error(request, f'CSV file should have exactly 4 columns. Found {len(csv_file_df.columns)} columns.')
                return redirect('profile')

            try:
                for _, row in csv_file_df.iterrows():
                    semester_year_interval = row[3].split(' ')[0]
                    semester_period_name = row[3].split(' ')[1]

                    semester = get_object_or_404(Semester, year_interval=semester_year_interval, period_name=semester_period_name)
                    course = get_object_or_404(Course, code=row[2])
                    student = get_object_or_404(Student, no=row[0])

                    for po in course.program_outcomes.all():
                        ProgramOutcomeResult.objects.update_or_create(
                            semester=semester,
                            course=course,
                            student=student,
                            program_outcome=po,
                            defaults={'satisfaction': 1}
                        )
                
                messages.success(request, 'File is successfuly processed.')
            except Exception as e:
                messages.error(request, f'Error occured: {e}')
            
    return redirect('profile')
            
            

def calculate_avgs(row):
    for idx in set(list(zip(*row.index))[0]):
        if row[idx].isna().sum() == len(row[idx]):
            row[idx, "AVG"] = 'NA'
        elif (row[idx].isna().sum() - 1) <= len(row[idx]) / 2:
            row[idx, "AVG"] = 0 if row[idx].mean() < 0.5 else 1
        else:
            row[idx, "AVG"] = 'IN'
    return row


@login_required
def export(request):
    """Exports the user uploaded entries filtered by the given parameters."""

    logger.info(f'Export requested by {request.user}.')
    export_report_form = ExportReportForm(request.POST)

    if request.method != 'POST' or not export_report_form.is_valid():
        return redirect('pc-calc:report')
    
    file_type = export_report_form.cleaned_data['export_type']
    semesters = export_report_form.cleaned_data['semesters']
    logger.debug(f'Exporting for semesters: {semesters}')

    tuples = list()
    for po in ProgramOutcome.objects.all():
        tuples += [(po.code, course.code) for course in po.course_set.all()] + [(po.code, 'AVG')]
    columns = pd.MultiIndex.from_tuples(tuples)

    report_df = pd.DataFrame(index=map(list, zip(*list(Student.objects.filter(graduated_on__isnull=True).values_list('no', 'name')) + [('Analysis', 'Total Number of Assessed Students'), ('Analysis', 'Number of Successful Students'), ('Analysis', 'Successful Student Percantage'), ('Analysis', 'Unsuccessful Student Percantage')])), columns=columns)

    for por in ProgramOutcomeResult.objects.filter(semester__in=semesters, student__graduated_on__isnull=True).order_by('semester__period_order_value'):
        report_df.loc[por.student.no, (por.program_outcome.code, por.course.code)] = por.satisfaction

    report_df.iloc[-4, :] = report_df.iloc[:-4, :].apply(lambda x: x.count(), axis=0) # Total Number of Assessed Students
    report_df.iloc[-3, :] = report_df.iloc[:-4, :].apply(lambda x: x.sum(), axis=0) # Number of Successful Students
    report_df.iloc[-2, :] = report_df.iloc[:-4, :].apply(lambda x: x.mean(), axis=0) # Successful Student Percantage
    report_df.iloc[-1, :] = report_df.iloc[:-4, :].apply(lambda x: (x.count() - x.sum()) / x.count() if x.count() > 0 else -1, axis=0) # Unsuccessful Student Percantage
    
    report_df.apply(calculate_avgs, axis=1)

    if file_type == 'xlsx':
        xlsx_buffer = io.BytesIO()
        with pd.ExcelWriter(xlsx_buffer) as xlwriter:
            report_df.to_excel(xlwriter)
        xlsx_buffer.seek(0)
        response = HttpResponse(xlsx_buffer.read(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response["Content-Disposition"] = 'attachment; filename="report.xlsx"'
    elif file_type == 'csv':
        csv_buffer = io.StringIO()
        report_df.to_csv(csv_buffer, index=True)
        csv_buffer.seek(0)
        response = HttpResponse(csv_buffer.read(), content_type = 'text/csv')
        response["Content-Disposition"] = 'attachment; filename="report.csv"'

    return response


@login_required
def export_diff(request):
    logger.info(f'Diff requested by {request.user}.')
    export_diff_report_form = ExportDiffReportForm(request.POST)

    if request.method != 'POST' or not export_diff_report_form.is_valid():
        return redirect('pc-calc:report')
    
    file_type = export_diff_report_form.cleaned_data['export_type']
    first_semesters = export_diff_report_form.cleaned_data['first_semesters']
    second_semesters = export_diff_report_form.cleaned_data['second_semesters']

    if first_semesters == second_semesters:
        messages.warning(request, 'The two semester ranges are equal.')
        return redirect('pc-calc:report')

    logger.debug(f'Diffing semesters: {first_semesters} and {second_semesters}')

    tuples = list()
    for po in ProgramOutcome.objects.all():
        tuples += [(po.code, course.code) for course in po.course_set.all()] + [(po.code, 'AVG')]
    columns = pd.MultiIndex.from_tuples(tuples)

    first_semesters_df = pd.DataFrame(index=Student.objects.filter(graduated_on__isnull=True).values_list('no', 'name'), columns=columns)
    for por in ProgramOutcomeResult.objects.filter(semester__pk__in=first_semesters, student__graduated_on__isnull=True).order_by('semester__period_order_value'):
        first_semesters_df.loc[por.student.no, (por.program_outcome.code, por.course.code)] = por.satisfaction
    first_semesters_df.apply(calculate_avgs, axis=1)

    second_semesters_df = pd.DataFrame(index=Student.objects.filter(graduated_on__isnull=True).values_list('no', 'name'), columns=columns)
    for por in ProgramOutcomeResult.objects.filter(semester__pk__in=second_semesters, student__graduated_on__isnull=True).order_by('semester__period_order_value'):
        second_semesters_df.loc[por.student.no, (por.program_outcome.code, por.course.code)] = por.satisfaction
    second_semesters_df.apply(calculate_avgs, axis=1)

    first_semesters_report_df = first_semesters_df.loc[:, (slice(None), 'AVG')]
    second_semesters_report_df = second_semesters_df.loc[:, (slice(None), 'AVG')]

    first_semesters_report_df.columns = first_semesters_report_df.columns.droplevel(1)
    second_semesters_report_df.columns = second_semesters_report_df.columns.droplevel(1)

    if first_semesters_report_df.equals(second_semesters_report_df):
        messages.warning(request, 'No difference between the chosen semester groups has been detected.')
        return redirect('pc-calc:report')
    
    report_df = first_semesters_report_df.compare(second_semesters_report_df, align_axis=0)
    fs_name = get_object_or_404(Semester, pk=first_semesters[-1])
    ss_name = get_object_or_404(Semester, pk=second_semesters[-1])

    report_df.rename(index={'self': str(fs_name),'other': str(ss_name)}, inplace=True)

    if file_type == 'xlsx':
        xlsx_buffer = io.BytesIO()
        with pd.ExcelWriter(xlsx_buffer) as xlwriter:
            report_df.to_excel(xlwriter)
        xlsx_buffer.seek(0)
        response = HttpResponse(xlsx_buffer.read(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response["Content-Disposition"] = 'attachment; filename="report_diffs.xlsx"'
    elif file_type == 'csv':
        csv_buffer = io.StringIO()
        report_df.to_csv(csv_buffer, index=True)
        csv_buffer.seek(0)
        response = HttpResponse(csv_buffer.read(), content_type = 'text/csv')
        response["Content-Disposition"] = 'attachment; filename="report_diffs.csv"'

    return response


@login_required
def course_report(request):
    logger.info(f'The list of not uploaded courses is requested by {request.user}.')
    semester_id = request.POST['semester']
    semester = get_object_or_404(Semester, pk=semester_id)
    uploaded_courses_set = set(chain.from_iterable(ProgramOutcomeFile.objects.filter(semester=semester).values_list('course')))

    return render(request, 'pc_calculator/upload_status.html', {'semester': semester, 'courses': semester.offered_courses.all(), 'ucourses_ids': uploaded_courses_set})


@login_required
def populate_students(request):
    if request.method == 'POST':
        stu_bulk_form = StudentBulkUploadForm(request.POST, request.FILES)

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


@login_required
@staff_member_required
def recalculate_all_pos(request):
    logger.info('Deleting existing records...')
    ProgramOutcomeResult.objects.all().delete()

    logger.info('All POs are recalculating...')
    all_po_files = ProgramOutcomeFile.objects.all()
    for po_count, program_outcome_file in enumerate(all_po_files):
        logger.debug(f'Read from file: {program_outcome_file.pc_file.name}. Remaining: {len(all_po_files) - (po_count + 1)}')

        with program_outcome_file.pc_file.open(mode='rb') as csv_file:
            contents_byte_str = csv_file.read()
            enc = force_decode(contents_byte_str)

        csv_file_df = pd.read_csv(program_outcome_file.pc_file.path, sep=None, engine='python', encoding=enc)
        file_pos = set(csv_file_df.columns[2:])

        for idx, row in csv_file_df.iterrows():
            student = Student.objects.filter(no=row.iloc[0], graduated_on__isnull=True).first()

            if student is not None:
                for po_idx, po in enumerate(file_pos):
                    program_outcome = ProgramOutcome.objects.get(code=po.strip())

                    if not row.iloc[po_idx + 2:].astype(str).str.contains('U').any():
                        ProgramOutcomeResult.objects.create(
                            student=student,
                            course=program_outcome_file.course,
                            program_outcome=program_outcome,
                            semester=program_outcome_file.semester,
                            satisfaction= 1 if str(row.iloc[po_idx + 2]) == "1" or str(row.iloc[po_idx + 2]) == "M" else 0
                        )
    
    messages.success(request, 'All student POs successfuly recalculated.')
    return redirect('profile')


@login_required
@user_passes_test(lambda user: user.is_superuser)
def dump_database(request):
    set_maintenance_mode(True)
    call_command('dbbackup', '--compress', '--clean', interactive=False)
    call_command('mediabackup', '--compress', '--clean', interactive=False)
    shutil.make_archive('/tmp/backup', 'zip', settings.BASE_DIR / 'backups')

    response = FileResponse(open('/tmp/backup.zip', 'rb'), as_attachment=True)
    # response["Content-Disposition"] = 'attachment; filename="backup.zip"'
    set_maintenance_mode(False)
    return response

@login_required
@user_passes_test(lambda user: user.is_superuser)
def restore_pclink(request):
    if request.method == 'POST':
        set_maintenance_mode(True)
        snapshot_form = RestoreBackupForm(request.POST, request.FILES)

        if snapshot_form.is_valid():
            with open('/tmp/backup.zip', 'wb') as backup_f:
                backup_f.write(snapshot_form.cleaned_data['snapshot_file'].read())
            shutil.rmtree(settings.BASE_DIR / 'backups', ignore_errors=True)
            shutil.unpack_archive('/tmp/backup.zip', settings.BASE_DIR / 'backups', 'zip')
            call_command('dbrestore', '--uncompress', interactive=False)
            call_command('dbrestore', '--uncompress', interactive=False)
            call_command('mediarestore', '--uncompress', interactive=False)
        set_maintenance_mode(False)
        messages.info(request, 'Database and media files are restored.')
    return redirect('profile')


@login_required
@user_passes_test(lambda user: user.is_superuser)
def remove_duplicates(request):
    unique_fields = ['student', 'course', 'program_outcome', 'semester']
    duplicates = ProgramOutcomeResult.objects.values(*unique_fields).order_by().annotate(max_id=Max('id'), count_id=Count('id')).filter(count_id__gt=1)
    
    for duplicate in duplicates:
        logger.debug(f'Removed duplicate record: {duplicate}')
        ProgramOutcomeResult.objects.filter(**{x: duplicate[x] for x in unique_fields}).exclude(id=duplicate['max_id']).delete()
    
    messages.success(request, f'{len(duplicates)} duplicate(s) is/are removed.')

    return redirect('profile')

def page_not_found(request, *args, **kwargs):
    return render(request, '404.html')


def server_error(request, *args, **kwargs):
    return render(request, '500.html')


def permission_denied(request, *args, **kwargs):
    return render(request, '403.html')


def bad_request(request, *args, **kwargs):
    return render(request, '400.html')
