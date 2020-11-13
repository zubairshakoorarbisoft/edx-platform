"""
Admin registration for Clearesult.
"""
from config_models.admin import KeyedConfigurationModelAdmin
from django.contrib import admin
from django.utils.translation import ugettext_lazy as _

from openedx.features.clearesult_features.forms import UserCreditsProfileAdminForm
from openedx.features.clearesult_features.models import (
    ClearesultCourseCredit,
    ClearesultCreditProvider,
    UserCreditsProfile,
    ClearesultUserProfile,
    ClearesultSiteConfiguration,
    ClearesultUserSiteProfile
)


class ClearesultCreditProviderAdmin(admin.ModelAdmin):
    """
    Admin config clearesult credit providers.
    """
    list_display = ('name', 'short_code')


class ClearesultCourseCreditsAdmin(admin.ModelAdmin):
    """
    Admin config for clearesult credits offered by the courses.
    """
    list_display = ('course_id', 'credit_type', 'credit_value')


class UserCreditsProfileAdmin(admin.ModelAdmin):
    """
    Admin config for user credit ids.
    """
    form = UserCreditsProfileAdminForm
    list_display = ('user', 'credit_type', 'credit_id', 'courses', 'earned_credits', 'total_credits')


class ClearesultSiteConfigurationAdmin(KeyedConfigurationModelAdmin):
    """
    Admin config for `ClearesultSiteConfiguration`.
    """
    search_fields = ('site__id', 'site__name')


class ClearesultUserSiteProfileAdmin(admin.ModelAdmin):
    """
    Admin config for `ClearesultUserSiteProfile`.
    """
    list_display = ('user', 'site')


admin.site.register(ClearesultCourseCredit, ClearesultCourseCreditsAdmin)
admin.site.register(ClearesultCreditProvider, ClearesultCreditProviderAdmin)
admin.site.register(UserCreditsProfile, UserCreditsProfileAdmin)
admin.site.register(ClearesultUserProfile)
admin.site.register(ClearesultSiteConfiguration, ClearesultSiteConfigurationAdmin)
admin.site.register(ClearesultUserSiteProfile, ClearesultUserSiteProfileAdmin)
