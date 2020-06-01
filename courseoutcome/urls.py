from django.urls import path

from . import views

app_name = "courseoutcome"
urlpatterns = [
    path("", views.upload, name="home"),
    path("query/", views.generate_query, name="query"),
    path("report/", views.CourseOutcomeAverageListView.as_view(), name="report"),
    path("report/<department>/<int:semester_id>/", views.CourseOutcomeAverageListView.as_view(), name="report-all"),
    path("report/<department>/<int:semester_id>/<course_outcome>/", views.CourseOutcomeAverageListView.as_view(), name="report-co"),
    path("report/<department>/<int:semester_id>/<course_outcome>/<student>/", views.CourseOutcomeAverageListView.as_view(), name="report-co-stu"),
    path("export/", views.export, name="export"),
    path("populate/", views.populate),
]