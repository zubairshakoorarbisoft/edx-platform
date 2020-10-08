"""
Admin registration for Clearesult.
"""

from django.contrib import admin
from openedx.features.clearesult_features.models import (
    ClearesultCourseCredit,
    ClearesultCreditProvider,
    UserCreditsProfile
)


class ClearesultCreditProviderAdmin(admin.ModelAdmin):
    """
    Admin config clearesult credit providers.
    """
    list_display = ['name', 'short_code']


class ClearesultCourseCreditsAdmin(admin.ModelAdmin):
    """
    Admin config for clearesult course credits.
    """
    list_display = ('course_id', 'credit_type', 'credit_value')


class UserCreditsProfileAdmin(admin.ModelAdmin):
    """
    Admin config for user credit ids.
    """
    list_display = ('user', 'credit_type', 'credit_id')


admin.site.register(ClearesultCourseCredit, ClearesultCourseCreditsAdmin)
admin.site.register(ClearesultCreditProvider, ClearesultCreditProviderAdmin)
admin.site.register(UserCreditsProfile, UserCreditsProfileAdmin)
