"""
Admin registration for Clearesult.
"""
from config_models.admin import KeyedConfigurationModelAdmin
from django.contrib import admin
from django.contrib import messages
from django.utils.translation import ugettext_lazy as _

from openedx.features.clearesult_features.forms import UserCreditsProfileAdminForm
from openedx.features.clearesult_features.models import (
    ClearesultCourseCredit,
    ClearesultCreditProvider,
    UserCreditsProfile,
    ClearesultUserProfile,
    ClearesultSiteConfiguration,
    ClearesultUserSiteProfile,
    ClearesultGroupLinkage,
    ClearesultCatalog,
    ClearesultCourse,
    ClearesultLocalAdmin,
    ClearesultGroupLinkedCatalogs,
    ClearesultCourseCompletion
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

class ClearesultCourseAdmin(admin.ModelAdmin):
    """
    Admin config clearesult courses.
    """
    list_display = ('course_id', 'site')

class ClearesultCatalogAdmin(admin.ModelAdmin):
    """
    Admin config clearesult credit providers.
    """
    list_display = ('name', 'site')

class ClearesultGroupLinkageAdmin(admin.ModelAdmin):
    """
    Admin config clearesult credit providers.
    """
    list_display = ('name', 'site')

    def get_actions(self, request):
        actions = super().get_actions(request)
        if 'delete_selected' in actions:
            del actions['delete_selected']
        return actions

    def delete_model(self, request, obj):
        """
        Don't delete group objects linked as a default group with some site
        """
        is_default = False
        clearesult_active_configs = ClearesultSiteConfiguration.objects.filter(enabled=True)
        for config in clearesult_active_configs:
            if config.default_group == obj:
                is_default = True
                messages.error(request, "Group is set as a dafault group of some site. Remove the linkgae first then try again.")
                break
        if not is_default:
            super().delete_model(request, obj)

class ClearesultLocalAdminInterface(admin.ModelAdmin):
    """
    Admin config clearesult credit providers.
    """
    list_display = ('site', 'user')


class ClearesultGroupLinkedCatalogsAdmin(admin.ModelAdmin):
    """
    Admin config clearesult credit providers.
    """
    list_display = ('id', 'group', 'catalog')


class ClearesultCourseCompletionAdmin(admin.ModelAdmin):
    list_display = ('user', 'course_id', 'completion_date', 'pass_date')


class ClearesultUserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'job_title', 'company', 'state_or_province', 'postal_code', 'extensions')


admin.site.register(ClearesultCourseCredit, ClearesultCourseCreditsAdmin)
admin.site.register(ClearesultCreditProvider, ClearesultCreditProviderAdmin)
admin.site.register(UserCreditsProfile, UserCreditsProfileAdmin)
admin.site.register(ClearesultUserProfile, ClearesultUserProfileAdmin)
admin.site.register(ClearesultSiteConfiguration, ClearesultSiteConfigurationAdmin)
admin.site.register(ClearesultUserSiteProfile, ClearesultUserSiteProfileAdmin)
admin.site.register(ClearesultCourse, ClearesultCourseAdmin)
admin.site.register(ClearesultCatalog, ClearesultCatalogAdmin)
admin.site.register(ClearesultGroupLinkage, ClearesultGroupLinkageAdmin)
admin.site.register(ClearesultLocalAdmin, ClearesultLocalAdminInterface)
admin.site.register(ClearesultGroupLinkedCatalogs, ClearesultGroupLinkedCatalogsAdmin)
admin.site.register(ClearesultCourseCompletion, ClearesultCourseCompletionAdmin)
