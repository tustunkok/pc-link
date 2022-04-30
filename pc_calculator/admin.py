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
admin.site.register(Curriculum)
