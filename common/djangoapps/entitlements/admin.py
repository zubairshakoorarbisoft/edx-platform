from django.contrib import admin
from .models import CourseEntitlement


@admin.register(CourseEntitlement)
class EntitlementAdmin(admin.ModelAdmin):
    list_display = ('user_id', 'root_course_id', 'enroll_end_date',
                    'mode', 'enrollment_course_id', 'is_active')
