"""
Helper functions for Clearesult credits.
"""

from logging import getLogger
from xmodule.modulestore.django import modulestore

from lms.djangoapps.grades.api import CourseGradeFactory
from openedx.features.clearesult_features.models import (
    ClearesultCourseCredit,
    ClearesultCreditProvider,
    UserCreditsProfile
)
logger = getLogger(__name__)


def get_available_credits_provider_list(course_key):
    available_providers_list = []
    used_course_providers_short_codes = [
        used_credit.credit_type.short_code for used_credit in ClearesultCourseCredit.objects.filter(
                course_id=course_key
            )
    ]
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


def generate_user_course_credits(course_id, user):
    course_credits = ClearesultCourseCredit.objects.filter(course_id=course_id)
    user_credits = UserCreditsProfile.objects.filter(user=user).prefetch_related('earned_course_credits')

    for user_credit in user_credits:
        for course_credit in course_credits:
            if (user_credit.credit_type == course_credit.credit_type and
                    course_credit not in user_credit.earned_course_credits.all()):
                user_credit.earned_course_credits.add(course_credit)
                logger.info(
                    'Add Credits => {} credits from credit_provider: {} have been added for user: {} and course {}.'.format(
                        course_credit.credit_value, course_credit.credit_type.name, user.email, course_id
                    )
                )

def remove_user_cousre_credits_if_exist(course_id, user):
    course_credits = ClearesultCourseCredit.objects.filter(course_id=course_id)
    user_credits = UserCreditsProfile.objects.filter(user=user).prefetch_related('earned_course_credits')

    for user_credit in user_credits:
        for course_credit in course_credits:
            if (user_credit.credit_type == course_credit.credit_type and
                    course_credit in user_credit.earned_course_credits.all()):
                user_credit.earned_course_credits.remove(course_credit)
                logger.info(
                    'Remove Credits => {} credits from credit_provider: {} have been removed for user: {} and course {}.'.format(
                        course_credit.credit_value, course_credit.credit_type.name, user.email, course_id
                    )
                )


def get_user_course_earned_credits(course_id, user):
    result = set();
    user_credits = UserCreditsProfile.objects.filter(user=user)

    for user_credit in user_credits:
        result = result.union(set(user_credit.earned_course_credits.filter(course_id=course_id)))

    return [{'name': r.credit_type.name, 'code': r.credit_type.short_code, 'credits': r.credit_value} for r in result]


def get_credit_provider_by_short_code(short_code):
    try:
        return ClearesultCreditProvider.objects.get(short_code=short_code)
    except ClearesultCreditProvider.DoesNotExist:
        return None


def list_user_credits_for_report(course_key, provider_filter=None):
    """
    Return info about user who have earned course credits after successfull completion of the courses.
    It will also apply filteration on the basis of given provider_filter.

    list_user_credits_for_report(course_key, provider_filter)
    would return [
        {
            'username': 'username1',
            'provider_id': 'user1_provider_id',
            'provider'': 'provider name'
            'email': 'email1,
            'course_id': 'course-v1:test1+course1+id1',
            'course_name': 'sample course name 1',
            'earned_credits': '1',
            'grade_percent': '0.83',
            'letter_grade': 'A'
        },
        {
            'username': 'username2',
            'provider_id': 'user2_provider_id',
            'provider'': 'provider name'
            'email': 'email2,
            'course_id': 'course-v1:test1+course1+id1',
            'course_name': 'sample course name 1',
            'earned_credits': '1',
            'grade_percent': '0.78',
            'letter_grade': 'PASS'
        },
        {
            'username': 'username1',
            'provider_id': 'user1_provider_id',
            'provider'': 'provider name'
            'email': 'email1,
            'course_id': 'course-v1:test1+course2+id2',
            'course_name': 'sample course name 2',
            'earned_credits': '3',
            'grade_percent': '0.80',
            'letter_grade': 'A'
        }
    ]

    Note that result will only contain results for the user earned credits.
    We will not include users who have completed the course but didn't get any credits.
    """
    data_list = []

    if provider_filter:
        user_credits_profiles = UserCreditsProfile.objects.filter(credit_type__short_code=provider_filter)
    else:
        user_credits_profiles = UserCreditsProfile.objects.all()

    for user_provider_profile in user_credits_profiles:
        user_credit_courses = user_provider_profile.earned_course_credits.all()
        if user_credit_courses.count() > 0:
            for course_credit in user_credit_courses:
                course_grade = CourseGradeFactory().read(user_provider_profile.user, course_key=course_credit.course_id)
                course = modulestore().get_course(course_credit.course_id)
                data = {
                    'username': user_provider_profile.user.username,
                    'email': user_provider_profile.user.email,
                    'user_provider_id': user_provider_profile.credit_id,
                    'provider_name': user_provider_profile.credit_type.name,
                    'provider_short_code':  user_provider_profile.credit_type.short_code,
                    'course_id': course_credit.course_id,
                    'course_name': course.display_name,
                    'earned_credits': course_credit.credit_value,
                    'grade_percent': course_grade.percent,
                    'letter_grade': course_grade.letter_grade
                }
                data_list.append(data)
        else:
            data = {
                'username': user_provider_profile.user.username,
                'email': user_provider_profile.user.email,
                'user_provider_id': user_provider_profile.credit_id,
                'provider_name': user_provider_profile.credit_type.name,
                'provider_short_code':  user_provider_profile.credit_type.short_code,
                'course_id': 'N/A',
                'course_name': 'N/A',
                'earned_credits': 0.0,
                'grade_percent': 'N/A',
                'letter_grade': 'N/A'
            }
            data_list.append(data)

    return data_list


def list_user_total_credits_for_report(course_key, provider_filter=None):
    """
    Return info about user accumulative earned credits. It will also apply filteration on the basis of
    given provider_filter.

    list_user_total_credits_for_report(course_key, provider_filter)
    would return [
        {
            'username': 'username1',
            'provider_id': 'user1_provider_id',
            'provider'': 'provider name'
            'email': 'email1,
            'total_earned_credits': '3',
        },
        {
            'username': 'username2',
            'provider_id': 'user2_provider_id',
            'provider'': 'provider name'
            'email': 'email2,
            'total_earned_credits': '1',
        },
        {
            'username': 'username1',
            'provider_id': 'user1_provider_id',
            'provider'': 'provider name'
            'email': 'email1,
            'total_earned_credits': 2
        }
    ]

    Note that result will only contain results for the users who have registered CUI for any Provider.
    """
    data_list = []

    if provider_filter:
        user_credits_profiles = UserCreditsProfile.objects.filter(credit_type__short_code=provider_filter)
    else:
        user_credits_profiles = UserCreditsProfile.objects.all()

    for user_provider_profile in user_credits_profiles:
        total_earned_credits = 0
        for course_credit in user_provider_profile.earned_course_credits.all():
            total_earned_credits += course_credit.credit_value

        data = {
            'username': user_provider_profile.user.username,
            'email': user_provider_profile.user.email,
            'user_provider_id': user_provider_profile.credit_id,
            'provider_name': user_provider_profile.credit_type.name,
            'provider_short_code':  user_provider_profile.credit_type.short_code,
            'total_earned_credits': total_earned_credits
        }
        data_list.append(data)

    return data_list
