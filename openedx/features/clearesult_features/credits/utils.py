"""
Helper functions for Clearesult credits.
"""

from logging import getLogger

from openedx.features.clearesult_features.models import (
    ClearesultCourseCredit,
    ClearesultCreditProvider,
    UserCreditsProfile
)

logger = getLogger(__name__)


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


def gennerate_user_course_credits(course_id, user):
    course_credits = ClearesultCourseCredit.objects.filter(course_id=course_id)
    user_credits = UserCreditsProfile.objects.filter(user=user)
    logger.info('=> Generating Course credits for user: {} and course: {}'.format(user.email, course_id._to_string()))

    for user_credit in user_credits:
        for course_credit in course_credits:
            if user_credit.credit_type == course_credit.credit_type and not course_credit in user_credit.earned_course_credits.all():
                user_credit.earned_course_credits.add(course_credit)
                logger.info(
                    '{} credits from credit_provider: {} have been added for user: {}.'.format(course_credit.credit_value, course_credit.credit_type.name, user.email))


def get_user_course_earned_credits(course_id, user):
    result = ClearesultCourseCredit.objects.none()
    user_credits = UserCreditsProfile.objects.filter(user=user)

    for user_credit in user_credits:
        result = result.union(user_credit.earned_course_credits.filter(course_id=course_id))

    return [{'name': r.credit_type.name, 'code': r.credit_type.short_code, 'credits': r.credit_value} for r in result]
