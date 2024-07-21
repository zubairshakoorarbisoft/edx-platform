"""
Django admin page for grades models
"""


from config_models.admin import ConfigurationModelAdmin, KeyedConfigurationModelAdmin
from django.contrib import admin

from lms.djangoapps.grades.config.forms import CoursePersistentGradesAdminForm
from lms.djangoapps.grades.config.models import (
    ComputeGradesSetting,
    CoursePersistentGradesFlag,
    PersistentGradesEnabledFlag
)
from lms.djangoapps.grades.models import PersistentSubsectionGrade

class CoursePersistentGradesAdmin(KeyedConfigurationModelAdmin):
    """
    Admin for enabling subsection grades on a course-by-course basis.
    Allows searching by course id.
    """
    form = CoursePersistentGradesAdminForm
    search_fields = ['course_id']
    fieldsets = (
        (None, {
            'fields': ('course_id', 'enabled'),
            'description': 'Enter a valid course id. If it is invalid, an error message will display.'
        }),
    )


class PersistentSubsectionGradeAdmin(admin.ModelAdmin):
    search_fields = ['user_id', 'course_id']


admin.site.register(PersistentSubsectionGrade, PersistentSubsectionGradeAdmin)
admin.site.register(CoursePersistentGradesFlag, CoursePersistentGradesAdmin)
admin.site.register(PersistentGradesEnabledFlag, ConfigurationModelAdmin)
admin.site.register(ComputeGradesSetting, ConfigurationModelAdmin)
