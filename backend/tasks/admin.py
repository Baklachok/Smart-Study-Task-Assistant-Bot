from django.contrib import admin
from django.contrib.admin import ModelAdmin

from .models import Task


@admin.register(Task)
class TaskAdmin(ModelAdmin):
    list_display = ("title", "user", "status", "priority", "due_at", "created_at")
    list_filter = ("status", "priority", "due_at")
    search_fields = ("title", "description", "user__username")
