from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from pc_calculator.models import *

admin.site.register(User, UserAdmin)
admin.site.register(ProgramOutcomeFile)
admin.site.register(Student)
admin.site.register(Course)
admin.site.register(ProgramOutcome)
admin.site.register(ProgramOutcomeResult)
admin.site.register(Semester)
