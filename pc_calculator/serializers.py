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
