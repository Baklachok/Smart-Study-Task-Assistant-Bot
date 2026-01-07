import logging
from drf_spectacular.utils import extend_schema
from rest_framework import generics, permissions

from .models import Course
from .serializers import CourseSerializer

logger = logging.getLogger(__name__)


@extend_schema(tags=["Courses"])
class CourseListCreateView(generics.ListCreateAPIView):
    serializer_class = CourseSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        logger.debug(
            "List courses",
            extra={"user_id": self.request.user.id},
        )
        return Course.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        course = serializer.save(user=self.request.user)
        logger.info(
            "Course created",
            extra={
                "user_id": self.request.user.id,
                "course_id": course.id,
            },
        )
