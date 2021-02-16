import django_filters

from pc_calculator.models import ProgramOutcomeResult

class ProgramOutcomeResultFilter(django_filters.FilterSet):
    class Meta:
        model = ProgramOutcomeResult
        fields = ['student', 'program_outcome']
