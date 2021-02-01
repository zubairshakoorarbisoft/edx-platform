import six
from celery import task
from django.test import RequestFactory
from student.models import CourseEnrollment
from openedx.core.lib.celery.task_utils import emulate_http_request

from openedx.features.clearesult_features.models import (
    ClearesultUserProfile, ClearesultCourse,
    ClearesultGroupLinkage, ClearesultGroupLinkedCatalogs,
    ClearesultLocalAdmin, ClearesultCourseCompletion
)


@task()
def enroll_students_to_mandatory_courses(request, users, courses):
    """
    enroll given users to the given clearesult_courses list if not already enrolled
    """
    from lms.djangoapps.instructor.views.api import students_update_enrollment

    fake_request = RequestFactory().get(u'/')
    fake_request.POST = {
        "reason": "Mandatory course",
        "role": "Learner",
        "auto_enroll": True,
        "email_students": True,
        "action": "enroll"
    }
    fake_request.method = 'POST'

    fake_request.user = request.user
    fake_request.site = request.site

    for course in courses:
        # filter out students who are already enrolled in the course
        not_enrolled_users = [user for user in users if not CourseEnrollment.is_enrolled(user, course.course_id)]
        fake_request.POST.update({
            "identifiers": ','.join([str(user.email) for user in not_enrolled_users])
        })
        students_update_enrollment(fake_request, course_id=six.text_type(course.course_id))


@task()
def check_and_enroll_group_users_to_mandatory_courses(request, group_id, newly_added_group_users):
    group_catalogs = ClearesultGroupLinkedCatalogs.objects.filter(group__id=group_id)

    for group_catalog in group_catalogs:
        mandatory_courses = group_catalog.mandatory_courses.all()
        if mandatory_courses:
            # calling task from task - use apply_async
            enroll_students_to_mandatory_courses(request, newly_added_group_users, mandatory_courses)
