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

from rest_framework import serializers
from pc_calculator.models import *

class ProgramOutcomeResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProgramOutcomeResult
        fields = [
            'student',
            'course',
            'program_outcome',
            'semester',
            'satisfaction'
        ]
        depth = 1

class StudentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Student
        fields = ['id', 'no', 'name']

class ProgramOutcomeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProgramOutcome
        fields = ['id', 'code']
