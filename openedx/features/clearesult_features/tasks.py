import logging
import six
from celery import task
from django.test import RequestFactory
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from student.models import CourseEnrollment
from openedx.core.lib.celery.task_utils import emulate_http_request

from openedx.features.clearesult_features.models import (
    ClearesultUserProfile, ClearesultCourse,
    ClearesultGroupLinkage, ClearesultGroupLinkedCatalogs,
    ClearesultLocalAdmin, ClearesultCourseCompletion
)


log = logging.getLogger('edx.celery.task')

@task()
def enroll_students_to_mandatory_courses(request_user_id, request_site_id, user_ids, course_ids):
    """
    enroll given users to the given clearesult_courses list if not already enrolled
    """
    from lms.djangoapps.instructor.views.api import students_update_enrollment

    log.info("TASK: enroll student to mandatory courses has been called.")
    users = []

    for user_id in user_ids:
        try:
            user_obj = User.objects.get(id=user_id)
            users.append(user_obj)
        except:
            pass

    fake_request = RequestFactory().get(u'/')
    fake_request.POST = {
        "reason": "Mandatory course",
        "role": "Learner",
        "auto_enroll": True,
        "email_students": True,
        "action": "enroll"
    }
    fake_request.method = 'POST'

    if request_user_id:
        try:
            request_user = User.objects.get(id=request_user_id)
            fake_request.user = request_user
        except User.DoesNotExist:
            pass

    if request_site_id:
        try:
            request_site = Site.objects.get(id=request_site_id)
            fake_request.site = request_site
        except Site.DoesNotExist:
            pass

    for course_id in course_ids:
        # filter out students who are already enrolled in the course
        not_enrolled_users = [user for user in users if not CourseEnrollment.is_enrolled(user, course_id)]
        user_emails = ','.join([str(user.email) for user in not_enrolled_users])

        fake_request.POST.update({
            "identifiers": user_emails
        })

        log.info("enroll users with email: {} to course: {}".format({user_emails}, {course_id}))
        students_update_enrollment(fake_request, course_id=course_id)


@task()
def check_and_enroll_group_users_to_mandatory_courses(req_user_id, req_site_id, group_id, newly_added_group_user_ids):
    log.info("TASK: check and enroll groups users to mandatory courses has been called for group_id: {}", group_id)
    group_catalogs = ClearesultGroupLinkedCatalogs.objects.filter(group__id=group_id)

    for group_catalog in group_catalogs:
        mandatory_courses = group_catalog.mandatory_courses.all()
        if mandatory_courses:
            # calling task from task - use apply_async
            enroll_students_to_mandatory_courses(
                req_user_id, req_site_id, newly_added_group_user_ids,
                [six.text_type(course.course_id) for course in mandatory_courses])
