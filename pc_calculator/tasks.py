from celery import shared_task
from django.shortcuts import get_object_or_404
import logging
import pandas as pd
from .utils import (calculate_avgs, calculate_unsats)
from .models import (ProgramOutcome, ProgramOutcomeResult, Student, Semester)

logger = logging.getLogger('pc_link_custom_logger')


@shared_task
def export_task(semesters, curriculum=None):
    tuples = list()
    for po in ProgramOutcome.objects.all():
        tuples += [(po.code, course.code) for course in po.course_set.all()] + [(po.code, f'{po.code} AVG'), (po.code, f'{po.code} #UNSAT')]
    columns = pd.MultiIndex.from_tuples(tuples)

    report_df = pd.DataFrame(index=map(list, zip(*list(Student.objects.filter(assigned_curriculum__pk=curriculum, graduated_on__isnull=True).values_list('no', 'name')) + [('Analysis', 'Total Number of Assessed Students'), ('Analysis', 'Number of Successful Students'), ('Analysis', 'Successful Student Percantage'), ('Analysis', 'Unsuccessful Student Percantage')])), columns=columns)

    for por in ProgramOutcomeResult.objects.filter(semester__in=semesters, student__graduated_on__isnull=True).order_by('semester__period_order_value'):
        report_df.loc[por.student.no, (por.program_outcome.code, por.course.code)] = por.satisfaction

    report_df.iloc[-4, :] = report_df.iloc[:-4, :].apply(lambda x: x.count(), axis=0) # Total Number of Assessed Students
    report_df.iloc[-3, :] = report_df.iloc[:-4, :].apply(lambda x: x.sum(), axis=0) # Number of Successful Students
    report_df.iloc[-2, :] = report_df.iloc[:-4, :].apply(lambda x: x.mean(), axis=0) # Successful Student Percantage
    report_df.iloc[-1, :] = report_df.iloc[:-4, :].apply(lambda x: (x.count() - x.sum()) / x.count() if x.count() > 0 else -1, axis=0) # Unsuccessful Student Percantage
    
    report_df = report_df.apply(calculate_avgs, axis=1)
    report_df = report_df.apply(calculate_unsats, axis=1)

    logger.debug(f'Finished creating report for semesters: {semesters}')

    return report_df

@shared_task
def export_diff_task(first_grp_semesters, second_grp_semesters, curriculum=None):
    logger.debug(f'Diffing semesters: {first_grp_semesters} and {second_grp_semesters} for curriculum {curriculum}')

    tuples = list()
    for po in ProgramOutcome.objects.all():
        tuples += [(po.code, course.code) for course in po.course_set.all()] + [(po.code, f'{po.code} AVG'), (po.code, f'{po.code} #UNSAT')]
    columns = pd.MultiIndex.from_tuples(tuples)

    first_semesters_df = pd.DataFrame(index=Student.objects.filter(assigned_curriculum__pk=curriculum, graduated_on__isnull=True).values_list('no', 'name'), columns=columns)
    for por in ProgramOutcomeResult.objects.filter(semester__pk__in=first_grp_semesters, student__assigned_curriculum__pk=curriculum, student__graduated_on__isnull=True).order_by('semester__period_order_value'):
        first_semesters_df.loc[por.student.no, (por.program_outcome.code, por.course.code)] = por.satisfaction
    first_semesters_df = first_semesters_df.apply(calculate_avgs, axis=1)

    second_semesters_df = pd.DataFrame(index=Student.objects.filter(assigned_curriculum__pk=curriculum, graduated_on__isnull=True).values_list('no', 'name'), columns=columns)
    for por in ProgramOutcomeResult.objects.filter(semester__pk__in=second_grp_semesters, student__assigned_curriculum__pk=curriculum, student__graduated_on__isnull=True).order_by('semester__period_order_value'):
        second_semesters_df.loc[por.student.no, (por.program_outcome.code, por.course.code)] = por.satisfaction
    second_semesters_df = second_semesters_df.apply(calculate_avgs, axis=1)

    if first_semesters_df.equals(second_semesters_df):
        messages.warning(request, 'No difference between the chosen semester groups has been detected.')
        return redirect('pc-calc:report')
    
    report_df = first_semesters_df.compare(second_semesters_df, align_axis=0)
    fs_name = get_object_or_404(Semester, pk=first_grp_semesters[-1])
    ss_name = get_object_or_404(Semester, pk=second_grp_semesters[-1])

    report_df.rename(index={'self': str(fs_name),'other': str(ss_name)}, inplace=True)

    return report_df