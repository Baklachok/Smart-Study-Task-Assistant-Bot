from django.urls import path
from .views import TaskListCreateView, TaskDetailView, HabitsReportView

urlpatterns = [
    path("", TaskListCreateView.as_view(), name="tasks-list-create"),
    path("<uuid:pk>/", TaskDetailView.as_view(), name="tasks-detail"),
    path("habits/", HabitsReportView.as_view(), name="tasks-habits"),
]
