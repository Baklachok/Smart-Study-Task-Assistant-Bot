from rest_framework import generics, permissions
from drf_spectacular.utils import extend_schema

from .models import Topic
from .serializers import TopicSerializer


@extend_schema(tags=["Topics"])
class TopicListCreateView(generics.ListCreateAPIView):
    serializer_class = TopicSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Topic.objects.filter(course__user=self.request.user)

    def perform_create(self, serializer):
        serializer.save()
