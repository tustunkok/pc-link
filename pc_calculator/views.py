from django.shortcuts import render
from django.contrib import messages
from django.views import generic
from django.urls import reverse_lazy
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin

from rest_framework import mixins
from rest_framework import generics
from rest_framework import permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from pc_calculator.models import *
from pc_calculator.serializers import *
from pc_calculator.forms import *
from pc_calculator.utils import *

import logging

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
        return ProgramOutcomeFile.objects.filter(user=self.request.user).order_by('-date_uploaded')

class ProgramOutcomeFileUpdateView(LoginRequiredMixin, generic.UpdateView):
    model = ProgramOutcomeFile
    fields = ['semester', 'course', 'pc_file']
    template_name = 'pc_calculator/update.html'
    success_url = reverse_lazy('pc-calc:manage')
    permission_classes = [IsAuthenticated]

    def form_valid(self, form):
        response = super().form_valid(form)

        semester = form.cleaned_data['semester']
        course = form.cleaned_data['course']
        pc_file = form.cleaned_data['pc_file']

        if handle_upload(self.request, course.code, semester.id, pc_file, self.request.user, logger, updated=True):
            messages.success(self.request, 'Program Outcome file is successfuly updated.')
        else:
            messages.warning(self.request, 'No student from the department exists in the uploaded file.')

        return response


class ProgramOutcomeFileDeleteView(LoginRequiredMixin, generic.DeleteView):
    model = ProgramOutcomeFile
    success_url = reverse_lazy('pc-calc:manage')
    template_name = 'pc_calculator/confirm_delete.html'
    permission_classes = [IsAuthenticated]

@login_required
def report_view(request):
    return render(request, 'pc_calculator/report.html', {})

@login_required
def upload_program_outcome_file(request):
    form = ProgramOutcomeForm(request.POST or None, request.FILES or None)

    if form.is_valid():
        course_code = form.cleaned_data['course']
        semester_pk = form.cleaned_data['semester']
        csvFile = form.cleaned_data['outcome_file']

        if handle_upload(request, course_code, semester_pk, csvFile, request.user, logger):
            messages.success(request, 'Program Outcome file is successfuly uploaded.')
        else:
            messages.warning(request, 'No student from the department exists in the uploaded file.')
    
    return render(request, 'pc_calculator/upload.html', { 'form': form })

@login_required
def export(request):
    logger.info(f'Export requested by {request.user}.')
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="report.csv"'

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