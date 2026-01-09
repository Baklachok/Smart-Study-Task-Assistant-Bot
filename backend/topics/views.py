from typing import Any

from django.db.models import QuerySet
from rest_framework import generics, permissions
from drf_spectacular.utils import extend_schema
from rest_framework.serializers import BaseSerializer

from .models import Topic
from .serializers import TopicSerializer


@extend_schema(tags=["Topics"])
class TopicListCreateView(generics.ListCreateAPIView):
    serializer_class = TopicSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self) -> QuerySet[Any]:
        queryset = Topic.objects.filter(course__user=self.request.user)

        course_id = self.request.query_params.get("course")
        if course_id:
            queryset = queryset.filter(course_id=course_id)

        return queryset

    def perform_create(self, serializer: BaseSerializer) -> None:
        serializer.save()
