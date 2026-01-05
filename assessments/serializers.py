from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from assessments.models import QuestionOption, Question, Exam, Submission, StudentAnswer
from assessments.services import GradingService


class QuestionOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuestionOption
        fields = ('id', 'text')


class QuestionSerializer(serializers.ModelSerializer):
    options = QuestionOptionSerializer(many=True, read_only=True)

    class Meta:
        model = Question
        fields = (
            'id',
            'text',
            'question_type',
            'options'
        )


class ExamSerializer(serializers.ModelSerializer):
    questions = QuestionSerializer(many=True, read_only=True)

    class Meta:
        model = Exam
        fields = (
            'id',
            'title',
            'description',
            'duration',
            'course',
            'metadata',
            'questions'
        )


class StudentAnswerSerializer(serializers.ModelSerializer):
    question = serializers.PrimaryKeyRelatedField(
        queryset=Question.objects.all(),
        error_messages={
            'does_not_exist': 'The specified question does not exist.'
        }
    )
    class Meta:
        model = StudentAnswer
        fields = (
            'question',
            'selected_option',
            'short_answer_text'
        )

    def validate(self, data):
        question = data.get('question')
        selected_option = data.get('selected_option')
        short_answer_text = data.get('short_answer_text')

        if question.question_type == 'MCQ':
            if not selected_option:
                raise ValidationError("MCQ questions require a selected option.")
            if selected_option.question != question:
                raise ValidationError({
                    "selected_option": "Selected option does not belong to the specified question."
                })

        elif question.question_type == 'SHORT':
            if not short_answer_text:
                raise ValidationError("Short answer questions require text.")

        return data


class SubmissionSerializer(serializers.ModelSerializer):
    answers = StudentAnswerSerializer(many=True)

    class Meta:
        model = Submission
        fields = (
            'id',
            'exam',
            'grade',
            'completed_at',
            'answers'
        )
        read_only_fields = (
            'grade',
            'completed_at',
            'student'
        )

    def validate(self, attrs):
        user = self.context.get('user')
        exam = attrs.get('exam')
        user_submission = Submission.objects.filter(student=user, exam=exam).first()
        # if user_submission.is_completed  or user_submission.answers.count() == exam.questions.count():
        #     raise serializers.ValidationError({
        #         "non_field_errors": "You have already completed this exam and cannot submit again."
        #     })
        return attrs

    def create(self, validated_data):
        answers_data = validated_data.pop('answers')

        submission, _ = Submission.objects.get_or_create(**validated_data)

        for answer_data in answers_data:
            question = answer_data.pop('question', None)
            StudentAnswer.objects.update_or_create(
                submission=submission,
                question=question,
                defaults=answer_data
            )
        GradingService.grade_submission(submission)
        return submission
