from django.urls import path

from . import views

urlpatterns = [
    path("", views.upload, name="courseoutcome-home"),
    path("report/", views.report, name="courseoutcome-report"),
    path("export/", views.export, name="courseoutcome-export"),
    path("create/", views.CourseOutcomeAverageCreateView.as_view(), name="courseoutcome-dm"),
    path("recalculate/", views.recalculate_everything),
    path("course/bulk_insert/", views.bulk_insert_courses),
    path("student/bulk_insert/", views.bulk_insert_students),
    path("courseoutcome/bulk_insert/", views.bulk_insert_courseoutcomes),
    path("student/bulk_insert/cmpe/", views.bulk_insert_students_cmpe),
]