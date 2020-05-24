from django import forms

from .models import Course, Semester, CourseOutcomeAverage

class CourseOutcomeForm(forms.Form):
    course_choices = [(course.code, f"{course.code} - {course.name}") for course in Course.objects.all()]
    semester_choices = [(semester.pk, f"{semester.year_interval} {semester.period_name}") for semester in Semester.objects.all()]
    
    course = forms.ChoiceField(choices=course_choices, label="Select a course:")
    semester = forms.ChoiceField(choices=semester_choices, label="Select a semester:")
    outcome_file = forms.FileField(label="Upload the PÇ File:")

class CourseOutcomeAverageForm(forms.ModelForm):
    class Meta:
        model = CourseOutcomeAverage
        fields = [
            "student",
            "course_outcome",
            "semester",
            "overall_satisfaction"
        ]