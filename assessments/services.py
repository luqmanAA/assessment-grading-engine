import logging
from abc import ABC, abstractmethod

from django.conf import settings
from django.utils import timezone
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from assessments.models import Submission
from helpers.llm_backends import LLMBackend, OpenAIBackend, GeminiBackend

logger = logging.getLogger(__name__)


class BaseGrader(ABC):
    def grade(self, expected: str, actual: str, template: str = None) -> float:
        """
        Compare expected answer and actual answer.
        Returns a score between 0.0 and 1.0.
        Commonly handles empty inputs and exact matches to save resources.
        """
        if not expected or not actual:
            return 0.0

        # Exact match check (case-insensitive and stripped)
        if expected.strip().lower() == actual.strip().lower():
            return 1.0

        return self.evaluate_result(expected, actual, template)

    @abstractmethod
    def evaluate_result(self, expected: str, actual: str, template: str = None) -> float:
        pass


class MockGrader(BaseGrader):

    def evaluate_result(self, expected: str, actual: str, template: str = None) -> float:
        try:
            expected = expected.strip().lower()
            actual = actual.strip().lower()
            vectorizer = TfidfVectorizer()
            tfidf_matrix = vectorizer.fit_transform([expected, actual])
            similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
            return float(similarity)
        except Exception as e:
            logger.error(f"Error in MockGrader: {e}")
            return 0.0


class LLMGrader(BaseGrader):

    def __init__(self):
        self.backend = self._get_backend()

    def _get_backend(self) -> LLMBackend:
        provider = getattr(settings, 'LLM_PROVIDER', '').upper()
        if provider == 'OPENAI':
            return OpenAIBackend()
        else:
            return GeminiBackend()

    def prepare_prompt(self, expected: str, actual: str, template: str = None) -> str:
        default_template = (
            "You are an automated grading assistant.\n"
            "Expected Answer: {expected}\n"
            "Student Answer: {actual}\n"
            "Grade the student's answer based on the expected answer.\n"
            "Return ONLY a numeric score between 0.0 and 1.0.\n"
            "0.0 means completely wrong, 1.0 means correct match."
        )
        active_template = template or default_template
        
        # Ensure placeholders exist in template
        if "{expected}" not in active_template or "{actual}" not in active_template:
             active_template += "\n\nContext for grading:\nExpected: {expected}\nStudent Answer: {actual}"

        return active_template.format(expected=expected, actual=actual)

    def evaluate_result(self, expected: str, actual: str, template: str = None) -> float:
        prompt = self.prepare_prompt(expected, actual, template)
        score = self.backend.generate_score(prompt)
        return score if score is not None else 0.0


class GradingFactory:
    @staticmethod
    def get_grader() -> BaseGrader:
        engine = getattr(settings, 'GRADING_ENGINE')
        if engine == 'LLM':
            return LLMGrader()

        return MockGrader()


class GradingService:

    @staticmethod
    def grade_submission(submission: Submission):
        grader = GradingFactory.get_grader()
        total_score = 0.0
        
        # Prefetch questions to optimize access if not already done
        answers = submission.answers.select_related('question', 'selected_option').all()

        for answer in answers:
            question = answer.question
            score = 0.0

            if question.question_type == 'MCQ':
                if answer.selected_option and (
                    question.expected_answer == str(answer.id) or # supporting ID match or
                    answer.selected_option.is_correct
                ):
                    score = 1.0
            elif question.question_type == 'SHORT':
                # Use exam's prompt template if available
                template = submission.exam.grading_prompt
                score = grader.grade(question.expected_answer, answer.short_answer_text or "", template=template)

            answer.score = score
            answer.save()
            total_score += score

        question_count = submission.exam.questions.count()
        submission.total_score = total_score
        submission.grade = (total_score / question_count) * 100 if question_count > 0 else 0.0
        
        if answers.count() == question_count:
            submission.is_completed = True
            submission.completed_at = timezone.now()

        submission.save()
