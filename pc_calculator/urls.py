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

from os import name
from django.urls import path
from rest_framework.urlpatterns import format_suffix_patterns
from pc_calculator import views, utils

app_name = "pc-calc"

urlpatterns = [
    path('api/program-outcome-results/', views.ProgramOutcomeResultList.as_view(), name='api-poresults'),
    path('api/students/', views.StudentList.as_view(), name='api-students'),
    path('api/program-outcomes/', views.ProgramOutcomeList.as_view(), name='api-po'),

    path('report/', views.report_view, name='report'),
    path('report/progress/<uuid>/', views.get_task_progress, name='task-progress'),
    path('report/download/<uuid>/<str:file_type>/', views.get_task_data, name='task-data'),
    path('upload/', views.upload_program_outcome_file, name='upload'),
    path('', views.upload_program_outcome_file, name='home'),
    path('export/', views.export, name='export'),
    path('export-diff/', views.export_diff, name='export-diff'),
    path('course-report/', views.course_report, name='course-report'),
    path('changelog/', views.changelog, name='changelog'),
    path('logs/', views.debug_logs, name='logs'),
    path('manage/', views.ProgramOutcomeFileListView.as_view(), name='manage'),
    path('manage/<int:pk>/update/', views.ProgramOutcomeFileUpdateView.as_view(), name='update'),
    path('manage/<int:pk>/delete/', views.ProgramOutcomeFileDeleteView.as_view(), name='delete'),
    path('manage/<int:pk>/delete-file-only/', views.ProgramOutcomeFileDeleteOnlyFileView.as_view(), name='delete-file-only'),

    path('upload/students/', views.populate_students, name='update-students'),
    path('upload/excempt-students/', views.handle_excempt_students, name='update-excempt-students'),
    path('recalculate-all-pos/', views.recalculate_all_pos, name='recalculate-all-pos'),
    path('create-backup-snapshot/', views.dump_pclink, name='create-backup-snapshot'),
    path('restore-pclink/', views.restore_pclink, name='restore-pclink'),
    path('remove-duplicates/', views.remove_duplicates, name='remove-duplicates'),
    path('upload/courses/', views.populate_courses_and_pos, name='populate-courses'),
    # path('upload/program-outcomes/', utils.populate_program_outcomes),
]

urlpatterns = format_suffix_patterns(urlpatterns)