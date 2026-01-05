from datetime import timedelta
from django.test import TestCase, override_settings
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status
from rest_framework.authtoken.models import Token
from .models import Exam, Question, QuestionOption, Submission, StudentAnswer
from .services import GradingFactory, MockGrader


class AuthTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.exam = Exam.objects.create(title="Test Exam", duration=timedelta(hours=1), course="CS101")

    def test_token_auth(self):
        # 1. Obtain token
        client = APIClient()
        response = client.post('/api/token-auth/', {'username': 'testuser', 'password': 'testpassword'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        token = response.data['token']
        
        # 2. Use token
        client.credentials(HTTP_AUTHORIZATION='Token ' + token)
        response = client.get('/api/exams/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_session_auth(self):
        client = APIClient()
        login = client.login(username='testuser', password='testpassword')
        self.assertTrue(login)
        response = client.get('/api/exams/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_unauthenticated_access(self):
        client = APIClient()
        response = client.get('/api/exams/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class GraderTestCase(TestCase):
    def test_mock_grader_exact_match(self):
        grader = MockGrader()
        score = grader.grade("Python is great", "Python is great")
        self.assertEqual(score, 1.0)

    def test_mock_grader_similarity(self):
        grader = MockGrader()
        score = grader.grade("Python is great", "Python is good")
        self.assertTrue(0.0 < score < 1.0)


class SubmissionTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='student', password='password')
        self.client.force_authenticate(user=self.user)
        
        self.exam = Exam.objects.create(title="Test Exam", duration=timedelta(hours=1), course="CS101")
        
        # MCQ Question
        self.q1 = Question.objects.create(
            exam=self.exam, text="What is 2+2?", question_type="MCQ", expected_answer="4"
        )
        self.q1_opt2 = QuestionOption.objects.create(question=self.q1, text="4", is_correct=True)
        
        # Short Answer Question
        self.q2 = Question.objects.create(
            exam=self.exam, text="Define AI.", question_type="SHORT", 
            expected_answer="Artificial Intelligence is simulation of human intelligence."
        )

    @override_settings(GRADING_ENGINE='MOCK', CELERY_TASK_ALWAYS_EAGER=True)
    def test_submission_grading(self):
        data = {
            "exam": self.exam.id,
            "answers": [
                {"question": self.q1.id, "selected_option": self.q1_opt2.id},
                {"question": self.q2.id, "short_answer_text": "Artificial Intelligence is simulation of human intelligence."}
            ]
        }
        
        response = self.client.post('/api/submissions/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        submission_id = response.data['id']
        submission = Submission.objects.get(id=submission_id)
        
        # Check grade (percentage)
        self.assertEqual(submission.grade, 100.0)
        # Check total score
        self.assertEqual(submission.total_score, 2.0)
