import logging
from typing import Any, cast

from django.db.models import QuerySet
from drf_spectacular.utils import extend_schema
from rest_framework import generics, permissions
from rest_framework.serializers import BaseSerializer

from .models import Course
from .serializers import CourseSerializer
from users.models import User

logger = logging.getLogger(__name__)


@extend_schema(tags=["Courses"])
class CourseListCreateView(generics.ListCreateAPIView):
    serializer_class = CourseSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Course.objects.none()

    def get_queryset(self) -> QuerySet[Any]:
        if getattr(self, "swagger_fake_view", False):
            return Course.objects.none()
        user = cast(User, self.request.user)
        logger.debug(
            "List courses",
            extra={"user_id": user.id},
        )
        return Course.objects.filter(user=user)

    def perform_create(self, serializer: BaseSerializer) -> None:
        user = cast(User, self.request.user)
        course = serializer.save(user=user)
        logger.info(
            "Course created",
            extra={
                "user_id": user.id,
                "course_id": course.id,
            },
        )
