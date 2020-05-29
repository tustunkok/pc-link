from django.urls import path

from . import views

app_name = "courseoutcome"
urlpatterns = [
    path("", views.upload, name="home"),
    path("report/", views.report, name="report"),
    path("export/", views.export, name="export"),
    path("create/", views.CourseOutcomeAverageCreateView.as_view(), name="dm"),
    path("recalculate/", views.recalculate_everything),
    path("course/bulk_insert/", views.bulk_insert_courses),
    path("student/bulk_insert/", views.bulk_insert_students),
    path("courseoutcome/bulk_insert/", views.bulk_insert_courseoutcomes),
    path("student/bulk_insert/cmpe/", views.bulk_insert_students_cmpe),
]