from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework.viewsets import ReadOnlyModelViewSet, ModelViewSet

from assessments.models import Exam, Submission
from assessments.serializers import ExamSerializer, SubmissionSerializer
from helpers.permissions import IsOwnerOnly


# Create your views here.

@extend_schema_view(
    list=extend_schema(summary="List all available exams"),
    retrieve=extend_schema(summary="Get details of a specific exam including questions and options")
)
class ExamViewSet(ReadOnlyModelViewSet):
    queryset = Exam.objects.prefetch_related('questions__options').all()
    serializer_class = ExamSerializer
    permission_classes = [IsAuthenticated]


@extend_schema_view(
    list=extend_schema(summary="List all submissions for the authenticated student"),
    retrieve=extend_schema(
        summary="Get details of a specific submission",
        responses={200: SubmissionSerializer, 403: None, 404: None}
    ),
    create=extend_schema(
        summary="Submit answers for an exam",
        description="Creates a new submission or updates an existing one if not already completed.",
        responses={201: SubmissionSerializer, 400: None, 401: None}
    )
)
class SubmissionViewSet(ModelViewSet):
    serializer_class = SubmissionSerializer
    permission_classes = (IsAuthenticated, IsOwnerOnly)
    http_method_names = ('get', 'post', 'head', 'options',)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                "id",
                type=int,
                location=OpenApiParameter.PATH
            )
        ]
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    def get_queryset(self):
        return Submission.objects.filter(student=self.request.user).select_related(
            'exam', 'student'
        ).prefetch_related(
            'answers',
            'answers__question',
            'answers__selected_option'
        )

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={'user': request.user})
        serializer.is_valid(raise_exception=True)
        submission = self.perform_create(serializer)

        headers = self.get_success_headers(serializer.data)
        return Response(SubmissionSerializer(submission).data, status=status.HTTP_201_CREATED, headers=headers)

    def perform_create(self, serializer):
        return serializer.save(student=self.request.user)