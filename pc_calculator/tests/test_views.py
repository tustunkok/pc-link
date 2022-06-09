
from django.test import TestCase
from django.test import Client
from django.urls import reverse
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils.timezone import activate
from pc_calculator.models import *
from pc_calculator.forms import *
import pandas as pd
import io
import os
import shutil

class LoggedInUploadViewTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        User.objects.create_user('testuser', 'test@example.com', '123456a.')

        curriculums = pd.read_csv(settings.BASE_DIR / 'test-documents' / 'curriculums.csv')
        for _, row in curriculums.iterrows():
            curr_courses = Course.objects.filter(code__in=row[1].split())
            Curriculum.objects.create(name=row[0]).member_courses.set(curr_courses)

        courses = pd.read_csv(settings.BASE_DIR / 'test-documents' / 'courses.csv')
        Course.objects.bulk_create(Course(code=row[0], name=row[1]) for _, row in courses.iterrows())

        students = pd.read_csv(settings.BASE_DIR / 'test-documents' / 'students.csv')
        Student.objects.bulk_create(Student(name=row[1], no=row[0], transfer_student=True if not pd.isna(row[2]) else False, double_major_student=True if not pd.isna(row[3]) else False, graduated_on=row[4] if not pd.isna(row[4]) else None, assigned_curriculum=Curriculum.objects.filter(name=row[5]).first()) for _, row in students.iterrows())

        program_outcomes = pd.read_csv(settings.BASE_DIR / 'test-documents' / 'program-outcomes.csv')
        ProgramOutcome.objects.bulk_create(ProgramOutcome(code=row[0], description=row[1]) for _, row in program_outcomes.iterrows())

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
            response = self.client.post(
                reverse('pc-calc:upload'),
                {
                    'course': 'CMPE113',
                    'semester': Semester.objects.get(year_interval='2020-2021', period_name='Fall').pk,
                    'outcome_file': fp
                }
            )
        
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
            response = self.client.post(reverse('pc-calc:upload'), {'course': 'CMPE113', 'semester': Semester.objects.get(year_interval='2020-2021', period_name='Fall').pk, 'outcome_file': fp})
        
        self.assertContains(response, 'successfuly uploaded')
        self.assertQuerysetEqual(ProgramOutcomeResult.objects.all(), ['[44629785700:CMPE113:PÇ13:[2020-2021:Fall]:1]', '[21098683261:CMPE113:PÇ13:[2020-2021:Fall]:1]', '[17763516392:CMPE113:PÇ13:[2020-2021:Fall]:1]', '[62475310697:CMPE113:PÇ13:[2020-2021:Fall]:0]', '[54296286776:CMPE113:PÇ13:[2020-2021:Fall]:1]', '[12031872585:CMPE113:PÇ13:[2020-2021:Fall]:1]'], ordered=False)

    def test_semicolon_correct_encoding(self):
        """
        Upload page should accept semicolon seperated CSV format.
        """
        with open(settings.BASE_DIR / 'test-documents' / 'pc_sub_cmpe113_semicolon_correct.csv', 'rb') as fp:
            response = self.client.post(reverse('pc-calc:upload'), {'course': 'CMPE113', 'semester': Semester.objects.get(year_interval='2020-2021', period_name='Fall').pk, 'outcome_file': fp})
        
        self.assertContains(response, 'successfuly uploaded')
        self.assertQuerysetEqual(ProgramOutcomeResult.objects.all(), ['[44629785700:CMPE113:PÇ13:[2020-2021:Fall]:1]', '[21098683261:CMPE113:PÇ13:[2020-2021:Fall]:1]', '[17763516392:CMPE113:PÇ13:[2020-2021:Fall]:1]', '[62475310697:CMPE113:PÇ13:[2020-2021:Fall]:0]', '[54296286776:CMPE113:PÇ13:[2020-2021:Fall]:1]', '[12031872585:CMPE113:PÇ13:[2020-2021:Fall]:1]'], ordered=False)

    def test_c1254_semicolon_correct_encoding(self):
        """
        Upload page should accept c1254 encoding format.
        """
        with open(settings.BASE_DIR / 'test-documents' / 'pc_sub_cmpe113_c1254_semicolon_correct.csv', 'rb') as fp:
            response = self.client.post(reverse('pc-calc:upload'), {'course': 'CMPE113', 'semester': Semester.objects.get(year_interval='2020-2021', period_name='Fall').pk, 'outcome_file': fp})
        
        self.assertContains(response, 'successfuly uploaded')
        self.assertQuerysetEqual(ProgramOutcomeResult.objects.all(), ['[44629785700:CMPE113:PÇ13:[2020-2021:Fall]:1]', '[21098683261:CMPE113:PÇ13:[2020-2021:Fall]:1]', '[17763516392:CMPE113:PÇ13:[2020-2021:Fall]:1]', '[62475310697:CMPE113:PÇ13:[2020-2021:Fall]:0]', '[54296286776:CMPE113:PÇ13:[2020-2021:Fall]:1]', '[12031872585:CMPE113:PÇ13:[2020-2021:Fall]:1]'], ordered=False)

    # def test_non_c1254_utf8_correct_encoding(self):
    #     """
    #     Upload page should accept UTF-8, c1254, or cp1252 encoding format.
    #     """
    #     with open(settings.BASE_DIR / 'test-documents' / 'pc_sub_cmpe113_diffenc_correct.csv', 'rb') as fp:
    #         response = self.client.post(reverse('pc-calc:upload'), {'course': 'CMPE113', 'semester': 3, 'outcome_file': fp})
        
    #     self.assertContains(response, 'The file encoding should be one of UTF-8, Windows 1254, or Windows 1252.')
    #     self.assertQuerysetEqual(ProgramOutcomeResult.objects.all(), [], ordered=False)

    def test_non_csv(self):
        """
        Upload page should not accept non-csv files.
        """
        with open(settings.BASE_DIR / 'test-documents' / 'pc_sub_cmpe113_correct.ods', 'rb') as fp:
            response = self.client.post(reverse('pc-calc:upload'), {'course': 'CMPE113', 'semester': 3, 'outcome_file': fp})
        
        self.assertContains(response, 'File type should be CSV. Not .ods')
        self.assertQuerysetEqual(ProgramOutcomeResult.objects.all(), [], ordered=False)
    
    def test_u_correct(self):
        """
        Upload page should accept but ignore students with U inputs.
        """
        with open(settings.BASE_DIR / 'test-documents' / 'pc_sub_cmpe113_U_correct.csv', 'rb') as fp:
            response = self.client.post(reverse('pc-calc:upload'), {'course': 'CMPE113', 'semester': Semester.objects.get(year_interval='2020-2021', period_name='Fall').pk, 'outcome_file': fp})
        
        self.assertContains(response, 'successfuly uploaded')
        self.assertQuerysetEqual(ProgramOutcomeResult.objects.all(), ['[44629785700:CMPE113:PÇ13:[2020-2021:Fall]:1]', '[17763516392:CMPE113:PÇ13:[2020-2021:Fall]:1]', '[62475310697:CMPE113:PÇ13:[2020-2021:Fall]:0]', '[54296286776:CMPE113:PÇ13:[2020-2021:Fall]:1]', '[12031872585:CMPE113:PÇ13:[2020-2021:Fall]:1]'], ordered=False)
    
    def test_multiple_entries_for_different_semesters(self):
        """
        Upload page should not touch the previously uploaded records.
        """
        with open(settings.BASE_DIR / 'test-documents' / 'pc_sub_cmpe113_correct.csv', 'rb') as fp:
            self.client.post(reverse('pc-calc:upload'), {'course': 'CMPE113', 'semester': Semester.objects.get(year_interval='2019-2020', period_name='Spring').pk, 'outcome_file': fp})
        
        with open(settings.BASE_DIR / 'test-documents' / 'pc_sub_cmpe113_nextsem_correct.csv', 'rb') as fp:
            self.client.post(reverse('pc-calc:upload'), {'course': 'CMPE113', 'semester': Semester.objects.get(year_interval='2020-2021', period_name='Fall').pk, 'outcome_file': fp})
        
        self.assertQuerysetEqual(ProgramOutcomeResult.objects.all(), ['[44629785700:CMPE113:PÇ13:[2019-2020:Spring]:1]', '[21098683261:CMPE113:PÇ13:[2019-2020:Spring]:1]', '[17763516392:CMPE113:PÇ13:[2019-2020:Spring]:1]', '[62475310697:CMPE113:PÇ13:[2019-2020:Spring]:0]', '[54296286776:CMPE113:PÇ13:[2019-2020:Spring]:1]', '[12031872585:CMPE113:PÇ13:[2019-2020:Spring]:1]', '[17763516392:CMPE113:PÇ13:[2020-2021:Fall]:1]', '[62475310697:CMPE113:PÇ13:[2020-2021:Fall]:1]', '[54296286776:CMPE113:PÇ13:[2020-2021:Fall]:1]'], ordered=False)
    
    def test_wrong_column_names(self):
        """
        Upload page should reject the malformed csv column names.
        """

        with open(settings.BASE_DIR / 'test-documents' / 'pc_sub_cmpe113_wrong_column_name.csv', 'rb') as fp:
            response = self.client.post(reverse('pc-calc:upload'), {'course': 'CMPE113', 'semester': 3, 'outcome_file': fp})
        
        self.assertContains(response, 'The headers of the file should be student_id, name, and exact PÇ codes.')
        self.assertQuerysetEqual(ProgramOutcomeResult.objects.all(), [], ordered=False)
    
    def test_correct_spaced_column_names(self):
        """
        Upload page should accept the spaced csv column names.
        """

        with open(settings.BASE_DIR / 'test-documents' / 'pc_sub_cmpe113_spaced_column_name.csv', 'rb') as fp:
            response = self.client.post(reverse('pc-calc:upload'), {'course': 'CMPE113', 'semester': Semester.objects.get(year_interval='2020-2021', period_name='Fall').pk, 'outcome_file': fp})
        
        self.assertContains(response, 'successfuly uploaded')
        self.assertQuerysetEqual(ProgramOutcomeResult.objects.all(), ['[44629785700:CMPE113:PÇ13:[2020-2021:Fall]:1]', '[21098683261:CMPE113:PÇ13:[2020-2021:Fall]:1]', '[17763516392:CMPE113:PÇ13:[2020-2021:Fall]:1]', '[62475310697:CMPE113:PÇ13:[2020-2021:Fall]:0]', '[54296286776:CMPE113:PÇ13:[2020-2021:Fall]:1]', '[12031872585:CMPE113:PÇ13:[2020-2021:Fall]:1]'], ordered=False)
    
    def test_non_u_all(self):
        """
        Upload page should reject the csv files with lines that does not have U in all columns.
        """

        with open(settings.BASE_DIR / 'test-documents' / 'pc_sub_se493_nonU_incorrect.csv', 'rb') as fp:
            response = self.client.post(reverse('pc-calc:upload'), {'course': 'SE493', 'semester': 3, 'outcome_file': fp})
        
        program_outcome_file_rec_count = ProgramOutcomeFile.objects.filter(semester=3, user__username='testuser', course__code='SE493').count()

        self.assertContains(response, 'The usage of U is wrong in lines 3.')
        self.assertQuerysetEqual(ProgramOutcomeResult.objects.all(), [], ordered=False)
        self.assertEqual(program_outcome_file_rec_count, 0)
        self.assertFalse(os.path.exists(settings.MEDIA_ROOT / 'uploads' / '2020-2021 Fall' / 'user_testuser' / 'pc_sub_se493_nonU_incorrect.csv'))
    
    def test_wrong_indicator_letter(self):
        """
        Upload page should reject the csv files with lines that does not have any of 1, 0, U, or M.
        """

        with open(settings.BASE_DIR / 'test-documents' / 'pc_sub_se493_wrong_indicator_letter.csv', 'rb') as fp:
            response = self.client.post(reverse('pc-calc:upload'), {'course': 'SE493', 'semester': 3, 'outcome_file': fp})
        
        program_outcome_file_rec_count = ProgramOutcomeFile.objects.filter(semester=3, user__username='testuser', course__code='SE493').count()

        self.assertContains(response, 'Following lines have unexpected characters: 7.')
        self.assertQuerysetEqual(ProgramOutcomeResult.objects.all(), [], ordered=False)
        self.assertEqual(program_outcome_file_rec_count, 0)
        self.assertFalse(os.path.exists(settings.MEDIA_ROOT / 'uploads' / '2020-2021 Fall' / 'user_testuser' / 'pc_sub_se493_wrong_indicator_letter.csv'))
    
    def test_any_delimiter(self):
        """
        Upload page should accept the csv files with any delimiters.
        """

        with open(settings.BASE_DIR / 'test-documents' / 'pc_sub_cmpe113_tab_delimited_correct.csv', 'rb') as fp:
            response = self.client.post(reverse('pc-calc:upload'), {'course': 'CMPE113', 'semester': Semester.objects.get(year_interval='2020-2021', period_name='Fall').pk, 'outcome_file': fp})
        
        self.assertContains(response, 'successfuly uploaded')
        self.assertQuerysetEqual(ProgramOutcomeResult.objects.all(), ['[44629785700:CMPE113:PÇ13:[2020-2021:Fall]:1]', '[21098683261:CMPE113:PÇ13:[2020-2021:Fall]:1]', '[17763516392:CMPE113:PÇ13:[2020-2021:Fall]:1]', '[62475310697:CMPE113:PÇ13:[2020-2021:Fall]:0]', '[54296286776:CMPE113:PÇ13:[2020-2021:Fall]:1]', '[12031872585:CMPE113:PÇ13:[2020-2021:Fall]:1]'], ordered=False)
        self.assertTrue(os.path.exists(settings.MEDIA_ROOT / 'uploads' / '2020-2021 Fall' / 'user_testuser' / 'pc_sub_cmpe113_tab_delimited_correct.csv'))



    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT / 'uploads' / '2020-2021 Fall' / 'user_testuser', ignore_errors=True)
        shutil.rmtree(settings.MEDIA_ROOT / 'uploads' / '2019-2020 Spring' / 'user_testuser', ignore_errors=True)
        shutil.rmtree(settings.MEDIA_ROOT / 'uploads' / '2019-2020 Fall' / 'user_testuser', ignore_errors=True)
        super().tearDownClass()


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
    
    # def test_multiple_semester_same_course_entered_csv_report(self):
    #     with open(settings.BASE_DIR / 'test-documents' / 'pc_sub_cmpe113_correct.csv', 'rb') as fp:
    #         self.client.post(reverse('pc-calc:upload'), {'course': 'CMPE113', 'semester': 1, 'outcome_file': fp})
        
    #     with open(settings.BASE_DIR / 'test-documents' / 'pc_sub_cmpe113_nextsem_correct.csv', 'rb') as fp:
    #         self.client.post(reverse('pc-calc:upload'), {'course': 'CMPE113', 'semester': 2, 'outcome_file': fp})
        
    #     response = self.client.post(reverse('pc-calc:export'), {'export_type': 'csv', 'semesters': ['1', '2']})
    #     downloaded_f = io.BytesIO(response.content)
    #     downloaded_df = pd.read_csv(downloaded_f, header=[0, 1], index_col=[0, 1])

    #     self.assertEqual(downloaded_df.loc['62475310697', ('PÇ13', 'CMPE113')][0], 1.0)
    #     self.assertEqual(downloaded_df.loc['62475310697', ('PÇ13', 'PÇ13 AVG')][0], 'IN')
    
    # def test_multiple_semester_same_course_entered_csv_majority_zero_report(self):
    #     with open(settings.BASE_DIR / 'test-documents' / 'pc_sub_se493_correct.csv', 'rb') as fp:
    #         self.client.post(reverse('pc-calc:upload'), {'course': 'SE493', 'semester': 1, 'outcome_file': fp})
        
    #     with open(settings.BASE_DIR / 'test-documents' / 'pc_sub_se493_nextsem_correct.csv', 'rb') as fp:
    #         self.client.post(reverse('pc-calc:upload'), {'course': 'SE493', 'semester': 2, 'outcome_file': fp})
        
    #     with open(settings.BASE_DIR / 'test-documents' / 'pc_sub_se493_nextnextsem_correct.csv', 'rb') as fp:
    #         self.client.post(reverse('pc-calc:upload'), {'course': 'SE493', 'semester': 3, 'outcome_file': fp})
        
    #     response = self.client.post(reverse('pc-calc:export'), {'export_type': 'csv', 'semesters': ['1', '2', '3']})
    #     downloaded_f = io.BytesIO(response.content)
    #     downloaded_df = pd.read_csv(downloaded_f, header=[0, 1], index_col=[0, 1])

    #     self.assertEqual(downloaded_df.loc['62475310697', ('PÇ11b', 'SE493')][0], 1.0)
    #     self.assertEqual(downloaded_df.loc['62475310697', ('PÇ11b', 'PÇ11b AVG')][0], 1.0)
    
    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT / 'uploads' / '2020-2021 Fall' / 'user_testuser', ignore_errors=True)
        shutil.rmtree(settings.MEDIA_ROOT / 'uploads' / '2019-2020 Spring' / 'user_testuser', ignore_errors=True)
        shutil.rmtree(settings.MEDIA_ROOT / 'uploads' / '2019-2020 Fall' / 'user_testuser', ignore_errors=True)
        super().tearDownClass()


class DBManagementTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        user = User.objects.create_user('testuser', 'test@example.com', '123456a.')
        user.is_superuser = True
        user.save()

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
    
    def test_remove_duplicate_po_results(self):
        """
        Remove Duplicate PO Results button should find and remove duplicate records.
        """
        with open(settings.BASE_DIR / 'test-documents' / 'pc_sub_cmpe113_correct.csv', 'rb') as fp:
            self.client.post(reverse('pc-calc:upload'), {'course': 'CMPE113', 'semester': 3, 'outcome_file': fp})
        
        ProgramOutcomeResult.objects.create(semester=Semester.objects.get(pk=3), course=Course.objects.get(code='CMPE113'), student=Student.objects.get(no='44629785700'), program_outcome=ProgramOutcome.objects.get(code='PÇ13'), satisfaction=1)
        
        self.assertQuerysetEqual(ProgramOutcomeResult.objects.all(), ['[44629785700:CMPE113:PÇ13:[2020-2021:Fall]:1]', '[44629785700:CMPE113:PÇ13:[2020-2021:Fall]:1]', '[21098683261:CMPE113:PÇ13:[2020-2021:Fall]:1]', '[17763516392:CMPE113:PÇ13:[2020-2021:Fall]:1]', '[62475310697:CMPE113:PÇ13:[2020-2021:Fall]:0]', '[54296286776:CMPE113:PÇ13:[2020-2021:Fall]:1]', '[12031872585:CMPE113:PÇ13:[2020-2021:Fall]:1]'], ordered=False)

        response = self.client.get(reverse('pc-calc:remove-duplicates'), follow=True)
        
        self.assertContains(response, '1 duplicate(s) is/are removed.')
        self.assertQuerysetEqual(ProgramOutcomeResult.objects.all(), ['[44629785700:CMPE113:PÇ13:[2020-2021:Fall]:1]', '[21098683261:CMPE113:PÇ13:[2020-2021:Fall]:1]', '[17763516392:CMPE113:PÇ13:[2020-2021:Fall]:1]', '[62475310697:CMPE113:PÇ13:[2020-2021:Fall]:0]', '[54296286776:CMPE113:PÇ13:[2020-2021:Fall]:1]', '[12031872585:CMPE113:PÇ13:[2020-2021:Fall]:1]'], ordered=False)
    
    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT / 'uploads' / '2020-2021 Fall' / 'user_testuser', ignore_errors=True)
        shutil.rmtree(settings.MEDIA_ROOT / 'uploads' / '2019-2020 Spring' / 'user_testuser', ignore_errors=True)
        shutil.rmtree(settings.MEDIA_ROOT / 'uploads' / '2019-2020 Fall' / 'user_testuser', ignore_errors=True)
        super().tearDownClass()
