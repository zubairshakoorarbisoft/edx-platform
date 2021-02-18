import json
import logging
import requests
import six

from celery import task
from celery_utils.logged_task import LoggedTask
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from student.models import CourseEnrollment
from django.test import RequestFactory

from openedx.core.lib.celery.task_utils import emulate_http_request
from openedx.features.clearesult_features.models import (
    ClearesultUserProfile, ClearesultCourse,
    ClearesultGroupLinkage, ClearesultGroupLinkedCatalogs,
    ClearesultLocalAdmin, ClearesultCourseCompletion
)
from opaque_keys.edx.keys import CourseKey
from lms.djangoapps.instructor.enrollment import enroll_email


log = logging.getLogger('edx.celery.task')

@task(base=LoggedTask)
def enroll_students_to_mandatory_courses(user_ids, course_ids, request_site_id, request_user_id=None):
    """
    enroll given users to the given clearesult_courses list if not already enrolled
    """
    from lms.djangoapps.instructor.views.api import students_update_enrollment
    from openedx.features.clearesult_features.utils import send_mandatory_courses_emails

    log.info("TASK: enroll student to mandatory courses has been called.")

    try:
        request_site = Site.objects.get(id=request_site_id)

        if request_user_id:
            request_user = User.objects.get(id=request_user_id)
        else:
            # any super user
            request_user = User.objects.filter(is_superuser=True)[0]

    except (User.DoesNotExist, Site.DoesNotExist):
        log.info("TASK Error: email task can not be called without request_user and request_site.")
        return

    users = []
    email_course_data = {}

    #convert user_ids list to users object list
    for user_id in user_ids:
        try:
            user_obj = User.objects.get(id=user_id)
            users.append(user_obj)
        except:
            log.info("TASK Error: user with id: {} does not request_site_id".format(user_id))

    for course_id in course_ids:
        # filter out students who are already enrolled in the course
        not_enrolled_users = [user for user in users if not CourseEnrollment.is_enrolled(user, course_id)]
        course_key = CourseKey.from_string(course_id)

        for user in not_enrolled_users:
            log.info("TASK: enroll user with email: {} in course_id: {}".format(user.email, course_id))
            before, after, enrollment_obj = enroll_email(course_key, user.email, True, False, {})

            before_status = before.to_dict()
            after_status = after.to_dict()

            # if before enrollment status was false and after status is true means user is now enrolled
            if (not before_status.get('enrollment', False)) and after_status.get('enrollment', False):
                if email_course_data.get(user.email):
                    new_value = email_course_data.get(user.email)
                    #avoid duplicate mandatory courses
                    if course_id not in new_value:
                        new_value.append(course_id)
                else:
                    new_value = [course_id]

                email_course_data.update({user.email: new_value})
            else:
                log.info(
                    "TASK Error: enrollment status didn't change for user: {}".format(user.email)
                )

    for key, value in email_course_data.items():
        if value:
            log.info("user: {} has been seccussfully enrolled in following courses: {}".format(key, value))
            send_mandatory_courses_emails([key], value, request_user, request_site)


@task(base=LoggedTask)
def check_and_enroll_group_users_to_mandatory_courses(group_id, newly_added_group_user_ids, req_site_id, req_user_id=None):

    log.info(
        "TASK: check and enroll groups users to mandatory courses has been called for group_id: {}".format(group_id))

    group_catalogs = ClearesultGroupLinkedCatalogs.objects.filter(group__id=group_id)

    all_madatory_courses = []

    # extract all mandatory courses fromm all linked catalogs of the group
    for group_catalog in group_catalogs:
        mandatory_courses = group_catalog.mandatory_courses.all()
        if mandatory_courses:
            # calling task from task - use apply_async
            all_madatory_courses.extend([six.text_type(course.course_id) for course in mandatory_courses])

    if len(all_madatory_courses):
        enroll_students_to_mandatory_courses(
            newly_added_group_user_ids, all_madatory_courses, req_site_id, req_user_id)


@task()
def call_drupal_logout_endpoint(email):
    api_credentials = getattr(settings, 'DRUPAL_LOGOUT_API_CREDENTIALS', {})
    if api_credentials == {}:
        log.info('You have not provided drupal logout API credentials.')
        return

    url = api_credentials.get('url', '') + email
    username = api_credentials.get('username', '')
    password = api_credentials.get('password', '')

    response = requests.get(url, auth=(username, password))

    if response.status_code == 200:
        log.info('Success: User with email {} has been successfully logged out from Drupal.'.format(email))
    else:
        log.info('Failed: User with email {} has not been logged out from Drupal.'.format(email))
