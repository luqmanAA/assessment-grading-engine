from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.status import HTTP_201_CREATED
from rest_framework.viewsets import ReadOnlyModelViewSet, ModelViewSet

from assessments.models import Exam, Submission
from assessments.serializers import ExamSerializer, SubmissionSerializer
from helpers.permissions import IsOwnerOnly


# Create your views here.

class ExamViewSet(ReadOnlyModelViewSet):
    queryset = Exam.objects.prefetch_related('questions').all()
    serializer_class = ExamSerializer
    permission_classes = [IsAuthenticated]


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
        return (
            Submission.objects.filter(student=self.request.user)
            .select_related('exam',)
            .prefetch_related('answers__question', 'answers__selected_option')
        )

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={'user': request.user})
        serializer.is_valid(raise_exception=True)
        submission = self.perform_create(serializer)

        headers = self.get_success_headers(serializer.data)
        return Response(SubmissionSerializer(submission).data, status=HTTP_201_CREATED, headers=headers)

    def perform_create(self, serializer):
        return serializer.save(student=self.request.user)