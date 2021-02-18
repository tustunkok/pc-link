from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from pc_calculator.models import *

class StudentAdmin(admin.ModelAdmin):
    search_fields = ['no', 'name', 'graduated_on']

class ProgramOutcomeResultAdmin(admin.ModelAdmin):
    search_fields = ['student__name', 'course__code', 'program_outcome__code', 'semester__year_interval']

admin.site.register(User, UserAdmin)
admin.site.register(ProgramOutcomeFile)
admin.site.register(Student, StudentAdmin)
admin.site.register(Course)
admin.site.register(ProgramOutcome)
admin.site.register(ProgramOutcomeResult, ProgramOutcomeResultAdmin)
admin.site.register(Semester)
