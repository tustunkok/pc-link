from celery import shared_task
import logging
import pandas as pd
import pickle
import io
from .utils import (calculate_avgs, calculate_unsats)
from .models import (ProgramOutcome, ProgramOutcomeResult, Student)

logger = logging.getLogger('pc_link_custom_logger')


@shared_task
def export_task(semesters):    
    logger.debug(f'Exporting for semesters: {semesters}')

    tuples = list()
    for po in ProgramOutcome.objects.all():
        tuples += [(po.code, course.code) for course in po.course_set.all()] + [(po.code, f'{po.code} AVG'), (po.code, f'{po.code} #UNSAT')]
    columns = pd.MultiIndex.from_tuples(tuples)

    report_df = pd.DataFrame(index=map(list, zip(*list(Student.objects.filter(graduated_on__isnull=True).values_list('no', 'name')) + [('Analysis', 'Total Number of Assessed Students'), ('Analysis', 'Number of Successful Students'), ('Analysis', 'Successful Student Percantage'), ('Analysis', 'Unsuccessful Student Percantage')])), columns=columns)

    for por in ProgramOutcomeResult.objects.filter(semester__in=semesters, student__graduated_on__isnull=True).order_by('semester__period_order_value'):
        report_df.loc[por.student.no, (por.program_outcome.code, por.course.code)] = por.satisfaction

    report_df.iloc[-4, :] = report_df.iloc[:-4, :].apply(lambda x: x.count(), axis=0) # Total Number of Assessed Students
    report_df.iloc[-3, :] = report_df.iloc[:-4, :].apply(lambda x: x.sum(), axis=0) # Number of Successful Students
    report_df.iloc[-2, :] = report_df.iloc[:-4, :].apply(lambda x: x.mean(), axis=0) # Successful Student Percantage
    report_df.iloc[-1, :] = report_df.iloc[:-4, :].apply(lambda x: (x.count() - x.sum()) / x.count() if x.count() > 0 else -1, axis=0) # Unsuccessful Student Percantage
    
    report_df = report_df.apply(calculate_avgs, axis=1)
    report_df = report_df.apply(calculate_unsats, axis=1)

    return report_df