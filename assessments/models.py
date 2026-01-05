from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone

from base.models import BaseModel


# Create your models here.


class Exam(BaseModel):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    duration = models.DurationField(help_text="Duration of the exam")
    course = models.CharField(max_length=255)
    metadata = models.JSONField(default=dict, blank=True)
    grading_prompt = models.TextField(
        null=True, blank=True,
        default="Grade the student's answer based on the expected answer. \n"
                "Return ONLY a numeric score between 0.0 and 1.0. \n"
                "Expected Answer: {expected}\nStudent Answer: {actual}\nScore 0.0-1.0:"
    )

    def __str__(self):
        return self.title


class Question(BaseModel):
    QUESTION_TYPES = (
        ('MCQ', 'Multiple Choice'),
        ('SHORT', 'Short Answer'),
    )
    exam = models.ForeignKey(Exam, related_name='questions', on_delete=models.CASCADE)
    question_type = models.CharField(max_length=10, choices=QUESTION_TYPES)
    text = models.TextField()
    expected_answer = models.TextField(help_text="Correct answer text or option")

    def __str__(self):
        return f"{self.question_type}: {self.text[:50]}"


class QuestionOption(BaseModel):
    question = models.ForeignKey(Question, related_name='options', on_delete=models.CASCADE)
    text = models.CharField(max_length=255)
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.text} for Question ID {self.question.id}"


class Submission(BaseModel):
    student = models.ForeignKey('auth.User', related_name='submissions', on_delete=models.CASCADE)
    exam = models.ForeignKey(Exam, related_name='submissions', on_delete=models.CASCADE)
    grade = models.DecimalField(
        null=True,
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)]
    )
    total_score = models.FloatField(null=True, validators=[MinValueValidator(0.0)])
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('student', 'exam')
        indexes = [
            models.Index(fields=[
                'student',
                'exam',
                'grade',
            ]),
        ]

    def __str__(self):
        return f"{self.student.username}: {self.exam.title}"


class StudentAnswer(BaseModel):
    submission = models.ForeignKey(Submission, related_name='answers', on_delete=models.CASCADE)
    question = models.ForeignKey(Question, related_name='student_answers', on_delete=models.CASCADE)
    selected_option = models.ForeignKey(QuestionOption, null=True, blank=True, on_delete=models.SET_NULL)
    short_answer_text = models.TextField(blank=True, null=True)
    score = models.FloatField(null=True, validators=[MinValueValidator(0.0)])

    class Meta:
        indexes = [
            models.Index(fields=[
                'submission',
                'question',
                'selected_option',
                'short_answer_text',
            ]),
        ]

    def __str__(self):
        return f"Answer to Question ID {self.question.id} in Submission ID {self.submission.id}"
