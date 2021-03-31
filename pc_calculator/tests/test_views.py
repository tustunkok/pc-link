
from django.test import TestCase
from django.test import Client
from django.urls import reverse
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from pc_calculator.models import *
from pc_calculator.forms import *
import pandas as pd

class UploadLoggedInViewTest(TestCase):

    def setUp(self):
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


    def test_pc_upload_view_accepts_upload(self):
        """
        This page should permit a CSV file upload up on a successful validation.
        Only the logged in users should reach out this page.
        """
        self.client.login(username='testuser', password='123456a.')
        with open(settings.BASE_DIR / 'test-documents' / 'pc_submission_file_cmpe113.csv', 'rb') as fp:
            csv_file = SimpleUploadedFile('pc_submission_file_cmpe113.csv', fp.read(), content_type="text/csv")
        
        response = self.client.post(reverse('pc-calc:upload'), {'course': 'CMPE113', 'semester': 3, 'outcome_file': csv_file})
        
        self.assertContains(response, 'successfuly uploaded')


    def test_user_logged_in(self):
        """
        This page should only be visible to user who are authenticated by
        PÇ-Link.
        """
        self.client.login(username='testuser', password='123456a.')
        response = self.client.get(reverse('pc-calc:upload'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Hi testuser,')
    
    def test_user_notlogged_in(self):
        """
        This page should not be visible to user who are not authenticated by
        PÇ-Link.
        """
        response = self.client.get(reverse('pc-calc:upload'))
        self.assertRedirects(response, '/accounts/login/?next=/upload/', status_code=302)
