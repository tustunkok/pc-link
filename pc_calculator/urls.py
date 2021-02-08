from django.urls import path
from rest_framework.urlpatterns import format_suffix_patterns
from pc_calculator import views, utils

app_name = "pc-calc"

urlpatterns = [
    path('api/program-outcome-results/', views.ProgramOutcomeResultList.as_view(), name='api-poresults'),
    path('api/students/', views.StudentList.as_view(), name='api-students'),
    path('api/program-outcomes/', views.ProgramOutcomeList.as_view(), name='api-po'),

    path('report/', views.report_view, name='report'),
    path('upload/', views.upload_program_outcome_file, name='upload'),
    path('', views.upload_program_outcome_file, name='home'),
    path('export/', views.export, name='export'),
    path('help/', views.help, name='help'),
    path('manage/', views.ProgramOutcomeFileListView.as_view(), name='manage'),
    path('manage/<int:pk>/update/', views.ProgramOutcomeFileUpdateView.as_view(), name='update'),
    path('manage/<int:pk>/delete/', views.ProgramOutcomeFileDeleteView.as_view(), name='delete'),

    path('upload/students/', utils.populate_students),
    path('upload/program-outcomes/', utils.populate_program_outcomes),
    path('upload/courses/', utils.populate_courses),
]

urlpatterns = format_suffix_patterns(urlpatterns)