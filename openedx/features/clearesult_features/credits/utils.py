"""
Helper functions for Clearesult credits.
"""

from openedx.features.clearesult_features.models import ClearesultCreditProvider, ClearesultCourseCredit


def get_available_credits_provider_list(course_key):
    available_providers_list = []
    used_course_providers_short_codes = [used_credit.credit_type.short_code for used_credit in ClearesultCourseCredit.objects.filter(course_id=course_key)]
    available_providers = ClearesultCreditProvider.objects.exclude(short_code__in=used_course_providers_short_codes)
    for provider in available_providers:
        available_providers_list.append({
            'name': provider.name,
            'short_code': provider.short_code,
        })
    return available_providers_list


def get_course_credits_list(course_key):
    course_credits = []
    for course_credit in ClearesultCourseCredit.objects.filter(course_id=course_key):
        course_credits.append({
            'credit_type_code': course_credit.credit_type.short_code,
            'credit_type_name': course_credit.credit_type.name,
            'credits': course_credit.credit_value
        })
    return course_credits


def get_all_credits_provider_list():
    all_providers_list = []
    for provider in ClearesultCreditProvider.objects.all():
        all_providers_list.append({
            'name': provider.name,
            'short_code': provider.short_code,
        })
    return all_providers_list
