import os
import logging
from abc import ABC, abstractmethod

from django.conf import settings
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from assessments.models import Submission

logger = logging.getLogger(__name__)


class BaseGrader(ABC):

    @abstractmethod
    def grade(self, expected: str, actual: str) -> float:
        """
        Compare expected answer and actual answer.
        Returns a score between 0.0 and 1.0.
        """
        pass


class MockGrader(BaseGrader):
    def grade(self, expected: str, actual: str) -> float:
        if not expected or not actual:
            return 0.0

        expected= expected.strip().lower()
        actual = actual.strip().lower()
        if expected == actual:
            return 1.0

        try:
            vectorizer = TfidfVectorizer()
            tfidf_matrix = vectorizer.fit_transform([expected, actual])
            similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
            return float(similarity)
        except Exception as e:
            logger.error(f"Error in MockGrader: {e}")
            return 0.0


class LLMGrader(BaseGrader):
    def __init__(self):
        api_key = getattr(settings, 'GOOGLE_API_KEY', os.getenv('GOOGLE_API_KEY'))
        if api_key:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-pro')
        else:
            self.model = None
            logger.warning("GOOGLE_API_KEY not found. LLMGrader will fail or return default scores.")

    def prepare_prompt(self, expected: str, actual: str, template: str) -> str:
        default_template = "Expected: {expected}\nStudent: {actual}\nResult: 0.0-1.0 only."
        active_template = template or default_template

        # checking if the template contains the required placeholders and add if otherwise
        if "{expected}" not in active_template or "{actual}" not in active_template:
            active_template += "\n\nContext for grading:\nExpected: {expected}\nStudent Answer: {actual}"

        return active_template.format(expected=expected, actual=actual)

    def grade(self, expected: str, actual: str, template: str = None) -> float:
        if not self.model:
            logger.error("LLMGrader is not configured with an API key.")
            return 0.0

        prompt = self.prepare_prompt(expected, actual, template)
        try:
            response = self.model.generate_content(prompt)
            score_text = response.text.strip()
            print(score_text)
            return float(score_text)
        except Exception as e:
            logger.error(f"Error in LLMGrader: {e}")
            return 0.0


class GradingFactory:
    @staticmethod
    def get_grader() -> BaseGrader:
        print(getattr(settings, 'GRADING_ENGINE'))
        print(settings.GRADING_ENGINE)
        engine = getattr(settings, 'GRADING_ENGINE')

        if engine == 'LLM':
            return LLMGrader()
        else:
            return MockGrader()


class GradingService:

    @staticmethod
    def grade_submission(submission: Submission):
        grader = GradingFactory.get_grader()
        print('grader', grader)
        total_score = 0.0

        for answer in submission.answers.all():
            question = answer.question
            score = 0.0

            if question.question_type == 'MCQ':
                if answer.selected_option and (
                    question.expected_answer == str(answer.id) or
                    answer.selected_option.is_correct
                ):
                    score = 1.0
            elif question.question_type == 'SHORT':
                score = grader.grade(question.expected_answer, answer.short_answer_text or "")

            answer.score = score
            answer.save()
            total_score += score

        question_count = submission.exam.questions.count()
        submission.total_score = total_score
        submission.grade = (total_score/question_count) *100 if question_count > 0 else 0.0
        if submission.answers.count() == question_count:
            submission.is_completed = True

        submission.save()