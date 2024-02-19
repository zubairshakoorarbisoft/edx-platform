"""
Admin Models
"""
"""
Django Admin page for SurveyReport.
"""


from django.contrib import admin
from .models import CourseCompletionEmailHistory


class CourseCompletionEmailHistoryAdmin(admin.ModelAdmin):
    """
    Admin to manage Course Completion Email History.
    """
    list_display = (
        'id', 'user', 'course_key', 'last_progress_email_sent',
    )
    search_fields = (
        'id', 'user__username', 'user__email', 'course_key',
    )

admin.site.register(CourseCompletionEmailHistory, CourseCompletionEmailHistoryAdmin)
