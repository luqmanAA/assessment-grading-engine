from django.core.management.base import BaseCommand
from datetime import timedelta
from assessments.models import Exam, Question, QuestionOption

class Command(BaseCommand):
    help = 'Generates sample data: Exams, Questions (MCQ & Short Answer), and Options.'

    def handle(self, *args, **kwargs):
        self.stdout.write("Generating sample data...")

        # Create Exam
        exam_title = "Introduction to Computer Science"
        exam, created = Exam.objects.get_or_create(
            title=exam_title,
            defaults={
                'description': "A basic exam covering Python and CS concepts.",
                'duration': timedelta(minutes=60),
                'course': "CS101",
                'metadata': {"level": "beginner"}
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS(f"Created Exam: {exam.title}"))
        else:
            self.stdout.write(f"Exam '{exam.title}' already exists.")

        # Create MCQ Question 1
        q1_text = "Which data type is immutable in Python?"
        q1, created = Question.objects.get_or_create(
            exam=exam,
            text=q1_text,
            defaults={
                'question_type': 'MCQ',
                'expected_answer': 'Tuple' 
            }
        )
        if created:
            QuestionOption.objects.create(question=q1, text="List", is_correct=False)
            QuestionOption.objects.create(question=q1, text="Dictionary", is_correct=False)
            QuestionOption.objects.create(question=q1, text="Tuple", is_correct=True)
            QuestionOption.objects.create(question=q1, text="Set", is_correct=False)
            self.stdout.write(f" - Created MCQ: {q1.text}")

        # Create MCQ Question 2
        q2_text = "What is the output of 2 ** 3?"
        q2, created = Question.objects.get_or_create(
            exam=exam,
            text=q2_text,
            defaults={
                'question_type': 'MCQ',
                'expected_answer': '8'
            }
        )
        if created:
            QuestionOption.objects.create(question=q2, text="6", is_correct=False)
            QuestionOption.objects.create(question=q2, text="8", is_correct=True)
            QuestionOption.objects.create(question=q2, text="9", is_correct=False)
            self.stdout.write(f" - Created MCQ: {q2.text}")

        # Create Short Answer Question 1
        q3_text = "Explain the difference between a list and a tuple."
        q3, created = Question.objects.get_or_create(
            exam=exam,
            text=q3_text,
            defaults={
                'question_type': 'SHORT',
                'expected_answer': "Lists are mutable and defined by square brackets, whereas tuples are immutable and defined by parentheses."
            }
        )
        if created:
            self.stdout.write(f" - Created Short Answer: {q3.text}")

        # Create Short Answer Question 2
        q4_text = "What does DRY stand for in software engineering?"
        q4, created = Question.objects.get_or_create(
            exam=exam,
            text=q4_text,
            defaults={
                'question_type': 'SHORT',
                'expected_answer': "Don't Repeat Yourself"
            }
        )
        if created:
            self.stdout.write(f" - Created Short Answer: {q4.text}")

        self.stdout.write(self.style.SUCCESS("Sample data generation complete."))
