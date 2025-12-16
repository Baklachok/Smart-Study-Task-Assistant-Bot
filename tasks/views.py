from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework import generics, permissions
from datetime import timedelta

from .models import Task
from .permissions import IsOwner
from .serializers import TaskSerializer


@extend_schema(request=TaskSerializer, tags=["Tasks"])
class TaskListCreateView(generics.ListCreateAPIView):
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = Task.objects.filter(user=self.request.user)
        filter_by = self.request.query_params.get("filter")
        now = timezone.now()

        if filter_by == "today":
            qs = qs.filter(due_at__date=now.date())
        elif filter_by == "week":
            end_week = now + timedelta(days=7)
            qs = qs.filter(due_at__date__range=(now.date(), end_week.date()))

        return qs

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


@extend_schema(request=TaskSerializer, tags=["Tasks"])
class TaskDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwner]
    queryset = Task.objects.all()
