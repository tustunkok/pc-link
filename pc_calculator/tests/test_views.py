
from django.test import TestCase
from django.test import Client
from django.urls import reverse
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from pc_calculator.models import *
from pc_calculator.forms import *
import pandas as pd
import io

class LoggedInUploadViewTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        User.objects.create_user('testuser', 'test@example.com', '123456a.')

        students = pd.read_csv(settings.BASE_DIR / 'test-documents' / 'students.csv')
        Student.objects.bulk_create(Student(name=row[1], no=row[0], transfer_student=True if not pd.isna(row[2]) else False, double_major_student=True if not pd.isna(row[3]) else False, graduated_on=row[4] if not pd.isna(row[4]) else None) for _, row in students.iterrows())

        program_outcomes = pd.read_csv(settings.BASE_DIR / 'test-documents' / 'program-outcomes.csv')
        ProgramOutcome.objects.bulk_create(ProgramOutcome(code=row[0], description=row[1]) for _, row in program_outcomes.iterrows())

        courses = pd.read_csv(settings.BASE_DIR / 'test-documents' / 'courses.csv')
        Course.objects.bulk_create(Course(code=row[0], name=row[1]) for _, row in courses.iterrows())

        po_courses = pd.read_csv(settings.BASE_DIR / 'test-documents' / 'program-outcomes-courses.csv')
        for _, row in po_courses.iterrows():
            rel_pos = ProgramOutcome.objects.filter(code__in=row[1].split('-'))
            Course.objects.get(code=row[0]).program_outcomes.add(*rel_pos)
        
        semesters = pd.read_csv(settings.BASE_DIR / 'test-documents' / 'semesters.csv')
        Semester.objects.bulk_create(Semester(year_interval=row[0], period_name=row[1], active=True) for _, row in semesters.iterrows())


    def setUp(self):
        self.client.login(username='testuser', password='123456a.')


    def test_accept_correct_file(self):
        """
        Upload page should permit a CSV file upload up on a successful validation.
        """
        with open(settings.BASE_DIR / 'test-documents' / 'pc_sub_cmpe113_correct.csv', 'rb') as fp:
            response = self.client.post(reverse('pc-calc:upload'), {'course': 'CMPE113', 'semester': 3, 'outcome_file': fp})
        
        self.assertContains(response, 'successfuly uploaded')
        self.assertQuerysetEqual(ProgramOutcomeResult.objects.all(), ['[44629785700:CMPE113:PÇ13:[2020-2021:Fall]:1]', '[21098683261:CMPE113:PÇ13:[2020-2021:Fall]:1]', '[17763516392:CMPE113:PÇ13:[2020-2021:Fall]:1]', '[62475310697:CMPE113:PÇ13:[2020-2021:Fall]:0]', '[54296286776:CMPE113:PÇ13:[2020-2021:Fall]:1]', '[12031872585:CMPE113:PÇ13:[2020-2021:Fall]:1]'], ordered=False)

    def test_not_accept_incorrect_file(self):
        """
        Upload page should not permit a CSV file upload up on a failed validation.
        No ProgramOutcomeResult records should be created.
        """
        with open(settings.BASE_DIR / 'test-documents' / 'pc_sub_cmpe113_wrong_pc.csv', 'rb') as fp:
            response = self.client.post(reverse('pc-calc:upload'), {'course': 'CMPE113', 'semester': 3, 'outcome_file': fp})
        
        self.assertContains(response, 'The program outcomes in the uploaded file do not match the program outcomes of the registered course for course CMPE113.')
        self.assertQuerysetEqual(ProgramOutcomeResult.objects.all(), [], ordered=False)
    
    def test_c1254_correct_encoding(self):
        """
        Upload page should accept c1254 encoding format.
        """
        with open(settings.BASE_DIR / 'test-documents' / 'pc_sub_cmpe113_c1254_correct.csv', 'rb') as fp:
            response = self.client.post(reverse('pc-calc:upload'), {'course': 'CMPE113', 'semester': 3, 'outcome_file': fp})
        
        self.assertContains(response, 'successfuly uploaded')
        self.assertQuerysetEqual(ProgramOutcomeResult.objects.all(), ['[44629785700:CMPE113:PÇ13:[2020-2021:Fall]:1]', '[21098683261:CMPE113:PÇ13:[2020-2021:Fall]:1]', '[17763516392:CMPE113:PÇ13:[2020-2021:Fall]:1]', '[62475310697:CMPE113:PÇ13:[2020-2021:Fall]:0]', '[54296286776:CMPE113:PÇ13:[2020-2021:Fall]:1]', '[12031872585:CMPE113:PÇ13:[2020-2021:Fall]:1]'], ordered=False)

    def test_semicolon_correct_encoding(self):
        """
        Upload page should accept semicolon seperated CSV format.
        """
        with open(settings.BASE_DIR / 'test-documents' / 'pc_sub_cmpe113_semicolon_correct.csv', 'rb') as fp:
            response = self.client.post(reverse('pc-calc:upload'), {'course': 'CMPE113', 'semester': 3, 'outcome_file': fp})
        
        self.assertContains(response, 'successfuly uploaded')
        self.assertQuerysetEqual(ProgramOutcomeResult.objects.all(), ['[44629785700:CMPE113:PÇ13:[2020-2021:Fall]:1]', '[21098683261:CMPE113:PÇ13:[2020-2021:Fall]:1]', '[17763516392:CMPE113:PÇ13:[2020-2021:Fall]:1]', '[62475310697:CMPE113:PÇ13:[2020-2021:Fall]:0]', '[54296286776:CMPE113:PÇ13:[2020-2021:Fall]:1]', '[12031872585:CMPE113:PÇ13:[2020-2021:Fall]:1]'], ordered=False)

    def test_c1254_semicolon_correct_encoding(self):
        """
        Upload page should accept c1254 encoding format.
        """
        with open(settings.BASE_DIR / 'test-documents' / 'pc_sub_cmpe113_c1254_semicolon_correct.csv', 'rb') as fp:
            response = self.client.post(reverse('pc-calc:upload'), {'course': 'CMPE113', 'semester': 3, 'outcome_file': fp})
        
        self.assertContains(response, 'successfuly uploaded')
        self.assertQuerysetEqual(ProgramOutcomeResult.objects.all(), ['[44629785700:CMPE113:PÇ13:[2020-2021:Fall]:1]', '[21098683261:CMPE113:PÇ13:[2020-2021:Fall]:1]', '[17763516392:CMPE113:PÇ13:[2020-2021:Fall]:1]', '[62475310697:CMPE113:PÇ13:[2020-2021:Fall]:0]', '[54296286776:CMPE113:PÇ13:[2020-2021:Fall]:1]', '[12031872585:CMPE113:PÇ13:[2020-2021:Fall]:1]'], ordered=False)

    # def test_non_c1254_utf8_correct_encoding(self):
    #     """
    #     Upload page should accept c1254 encoding format.
    #     """
    #     with open(settings.BASE_DIR / 'test-documents' / 'pc_sub_cmpe113_utf7_correct.csv', 'rb') as fp:
    #         response = self.client.post(reverse('pc-calc:upload'), {'course': 'CMPE113', 'semester': 3, 'outcome_file': fp})
        
    #     self.assertContains(response, f'File encoding cannot be determined. It should be one of {["cp1254", "utf_8", "cp1252"]}')
    #     self.assertQuerysetEqual(ProgramOutcomeResult.objects.all(), [], ordered=False)

    def test_non_csv(self):
        """
        Upload page should not accept non-csv files.
        """
        with open(settings.BASE_DIR / 'test-documents' / 'pc_sub_cmpe113_correct.ods', 'rb') as fp:
            response = self.client.post(reverse('pc-calc:upload'), {'course': 'CMPE113', 'semester': 3, 'outcome_file': fp})
        
        self.assertContains(response, 'Wrong file type: .ods. It should be a CSV file.')
        self.assertQuerysetEqual(ProgramOutcomeResult.objects.all(), [], ordered=False)
    
    def test_u_correct(self):
        """
        Upload page should accept but ignore students with U inputs.
        """
        with open(settings.BASE_DIR / 'test-documents' / 'pc_sub_cmpe113_U_correct.csv', 'rb') as fp:
            response = self.client.post(reverse('pc-calc:upload'), {'course': 'CMPE113', 'semester': 3, 'outcome_file': fp})
        
        self.assertContains(response, 'successfuly uploaded')
        self.assertQuerysetEqual(ProgramOutcomeResult.objects.all(), ['[44629785700:CMPE113:PÇ13:[2020-2021:Fall]:1]', '[17763516392:CMPE113:PÇ13:[2020-2021:Fall]:1]', '[62475310697:CMPE113:PÇ13:[2020-2021:Fall]:0]', '[54296286776:CMPE113:PÇ13:[2020-2021:Fall]:1]', '[12031872585:CMPE113:PÇ13:[2020-2021:Fall]:1]'], ordered=False)
    
    def test_multiple_entries_for_different_semesters(self):
        """
        Upload page should not touch the previously uploaded records.
        """
        with open(settings.BASE_DIR / 'test-documents' / 'pc_sub_cmpe113_correct.csv', 'rb') as fp:
            self.client.post(reverse('pc-calc:upload'), {'course': 'CMPE113', 'semester': 2, 'outcome_file': fp})
        
        with open(settings.BASE_DIR / 'test-documents' / 'pc_sub_cmpe113_nextsem_correct.csv', 'rb') as fp:
            self.client.post(reverse('pc-calc:upload'), {'course': 'CMPE113', 'semester': 3, 'outcome_file': fp})
        
        self.assertQuerysetEqual(ProgramOutcomeResult.objects.all(), ['[44629785700:CMPE113:PÇ13:[2019-2020:Spring]:1]', '[21098683261:CMPE113:PÇ13:[2019-2020:Spring]:1]', '[17763516392:CMPE113:PÇ13:[2019-2020:Spring]:1]', '[62475310697:CMPE113:PÇ13:[2019-2020:Spring]:0]', '[54296286776:CMPE113:PÇ13:[2019-2020:Spring]:1]', '[12031872585:CMPE113:PÇ13:[2019-2020:Spring]:1]', '[17763516392:CMPE113:PÇ13:[2020-2021:Fall]:1]', '[62475310697:CMPE113:PÇ13:[2020-2021:Fall]:1]', '[54296286776:CMPE113:PÇ13:[2020-2021:Fall]:1]'], ordered=False)


class ExportViewTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        User.objects.create_user('testuser', 'test@example.com', '123456a.')

        students = pd.read_csv(settings.BASE_DIR / 'test-documents' / 'students.csv')
        Student.objects.bulk_create(Student(name=row[1], no=row[0], transfer_student=True if not pd.isna(row[2]) else False, double_major_student=True if not pd.isna(row[3]) else False, graduated_on=row[4] if not pd.isna(row[4]) else None) for _, row in students.iterrows())

        program_outcomes = pd.read_csv(settings.BASE_DIR / 'test-documents' / 'program-outcomes.csv')
        ProgramOutcome.objects.bulk_create(ProgramOutcome(code=row[0], description=row[1]) for _, row in program_outcomes.iterrows())

        courses = pd.read_csv(settings.BASE_DIR / 'test-documents' / 'courses.csv')
        Course.objects.bulk_create(Course(code=row[0], name=row[1]) for _, row in courses.iterrows())

        po_courses = pd.read_csv(settings.BASE_DIR / 'test-documents' / 'program-outcomes-courses.csv')
        for _, row in po_courses.iterrows():
            rel_pos = ProgramOutcome.objects.filter(code__in=row[1].split('-'))
            Course.objects.get(code=row[0]).program_outcomes.add(*rel_pos)
        
        semesters = pd.read_csv(settings.BASE_DIR / 'test-documents' / 'semesters.csv')
        Semester.objects.bulk_create(Semester(year_interval=row[0], period_name=row[1], active=True) for _, row in semesters.iterrows())


    def setUp(self):
        self.client.login(username='testuser', password='123456a.')
    
    def test_multiple_semester_same_course_entered_csv_report(self):
        with open(settings.BASE_DIR / 'test-documents' / 'pc_sub_cmpe113_correct.csv', 'rb') as fp:
            self.client.post(reverse('pc-calc:upload'), {'course': 'CMPE113', 'semester': 1, 'outcome_file': fp})
        
        with open(settings.BASE_DIR / 'test-documents' / 'pc_sub_cmpe113_nextsem_correct.csv', 'rb') as fp:
            self.client.post(reverse('pc-calc:upload'), {'course': 'CMPE113', 'semester': 2, 'outcome_file': fp})
        
        response = self.client.post(reverse('pc-calc:export'), {'export_type': 'csv', 'semesters': ['1', '2']})
        downloaded_f = io.BytesIO(response.content)
        downloaded_df = pd.read_csv(downloaded_f, header=[0, 1], index_col=[0, 1])

        self.assertEqual(downloaded_df.loc[62475310697, ('PÇ13', 'CMPE113')][0], 1.0)
        self.assertEqual(downloaded_df.loc[62475310697, ('PÇ13', 'AVG')][0], 'IN')
    
    def test_multiple_semester_same_course_entered_csv_majority_zero_report(self):
        with open(settings.BASE_DIR / 'test-documents' / 'pc_sub_se493_correct.csv', 'rb') as fp:
            self.client.post(reverse('pc-calc:upload'), {'course': 'SE493', 'semester': 1, 'outcome_file': fp})
        
        with open(settings.BASE_DIR / 'test-documents' / 'pc_sub_se493_nextsem_correct.csv', 'rb') as fp:
            self.client.post(reverse('pc-calc:upload'), {'course': 'SE493', 'semester': 2, 'outcome_file': fp})
        
        with open(settings.BASE_DIR / 'test-documents' / 'pc_sub_se493_nextnextsem_correct.csv', 'rb') as fp:
            self.client.post(reverse('pc-calc:upload'), {'course': 'SE493', 'semester': 3, 'outcome_file': fp})
        
        response = self.client.post(reverse('pc-calc:export'), {'export_type': 'csv', 'semesters': ['1', '2', '3']})
        downloaded_f = io.BytesIO(response.content)
        downloaded_df = pd.read_csv(downloaded_f, header=[0, 1], index_col=[0, 1])

        self.assertEqual(downloaded_df.loc[62475310697, ('PÇ11b', 'SE493')][0], 1.0)
        self.assertEqual(downloaded_df.loc[62475310697, ('PÇ11b', 'AVG')][0], 1.0)

