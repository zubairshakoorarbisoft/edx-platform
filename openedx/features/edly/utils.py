import logging

from courseware.courses import get_course_by_id
from django.conf import settings
from edx_ace import ace
from celery.task import task
from edx_ace.recipient import Recipient
from lms.djangoapps.instructor.enrollment import send_mail_to_student
from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers
from openedx.features.edly.message_types import ChangesEmail
from student.models import CourseEnrollment
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.exceptions import InvalidLocationError, ItemNotFoundError

log = logging.getLogger(__name__)
TASK_LOG = logging.getLogger(__name__)

COURSE_OUTLINE_CATEGORIES = ['vertical', 'sequential', 'chapter']


def notify_students_about_xblock_changes(xblock, publish):
    """
    This function is responsible for calling the related function by checking the xblock category.

    :param xblock: Block of courses which has been published.
    :param publish: Param to check if xblock is going to be published.
    """
    if (publish == 'make_public' and xblock.category in COURSE_OUTLINE_CATEGORIES
            and not xblock.visible_to_staff_only):
        _handle_section_publish(xblock)
    elif xblock.category == 'handout':
        _handle_handout_changes(xblock)


def get_email_params(xblock):
    """
    This function is responsible for generating the email_params which we are
    going to send to students for any changes in course.

    :param xblock: xblock which is modified/created
    :return: Dict containing the data for email.
    """
    email_params = {}
    course = get_course_by_id(xblock.location.course_key)
    email_params['course_name'] = course.display_name_with_default
    email_params['display_name'] = xblock.display_name
    email_params['site_name'] = configuration_helpers.get_value(
        'SITE_NAME',
        settings.SITE_NAME
    )
    return email_params


def _handle_section_publish(xblock):
    """
    This function will send email to the enrolled students in the case
    of any outline changes like section, subsection, unit publish.

    :param xblock: xblock which is modified/created
    """
    email_params = get_email_params(xblock)
    students = get_course_enrollments(xblock.location.course_key)

    if xblock.category == 'vertical':
        published_unit_url = _get_published_unit_url(xblock)
        email_params['change_type'] = 'Unit'
        email_params['change_url'] = published_unit_url
    elif xblock.category == 'sequential':
        subsection_url = '{lms_base_url}/courses/{course_id}/course/#{subsection_usage_key}'.format(
            lms_base_url=settings.LMS_ROOT_URL,
            course_id=xblock.location.course_key,
            subsection_usage_key=xblock.location
        )
        email_params['change_url'] = subsection_url
        email_params['change_type'] = 'Sub Section'
    else:
        section_url = '{lms_base_url}/courses/{course_id}/course/#{section_usage_key}'.format(
            lms_base_url=settings.LMS_ROOT_URL,
            course_id=xblock.location.course_key,
            section_usage_key=xblock.location
        )
        email_params['change_type'] = 'Section'
        email_params['change_url'] = section_url
    send_bulk_mail_to_students.delay(students, email_params)


def _handle_handout_changes(xblock):
    pass


def get_xblock(usage_key):
    """
    This function will get xblock.

    :param usage_key: usage_key of xblock we are getting.
    :return: xblock
    """
    store = modulestore()
    with store.bulk_operations(usage_key.course_key):
        try:
            return store.get_item(usage_key, depth=None)
        except ItemNotFoundError:
            log.error("Can't find parent xblock.")
            return None
        except InvalidLocationError:
            log.error("Can't find parent/item by location.")
            return None


def _get_published_unit_url(xblock):
    """
    This function will generate the url of unit published

    :param xblock: Unit xblock published
    :return: Learner site url of unit.

    URL pattern:  LMS_ROOT_URL/courses/courseware/SECTION_URL_NAME/SUBSECTION_URL_NAME/UNIT_URL_NAME/TAB_NUM?
                    activate_block_id=UNIT_XBLOCK_USAGE_KEY
    """
    published_unit_url = None
    if xblock.parent:
        subsection_xblock = get_xblock(xblock.parent)
        if subsection_xblock:
            section_xblock = get_xblock(subsection_xblock.parent)
            if section_xblock:
                subsection_url_name = subsection_xblock.url_name
                section_url_name = section_xblock.url_name
                published_unit_url = '{lms_base_url}/courses/{course_id}/courseware/{section_url_name}/' \
                                     '{subsection_url_name}/?activate_block_id={unit_usage_key}'.format(
                    lms_base_url=settings.LMS_ROOT_URL,
                    course_id=xblock.location.course_key,
                    section_url_name=section_url_name,
                    subsection_url_name=subsection_url_name,
                    unit_usage_key=xblock.location)
    return published_unit_url


@task(bind=True)
def send_bulk_mail_to_students(students, param_dict):
    """
    This task is responsible for sending the email to all of the students using the ChangesEmail Message type.

    :param students: List of enrolled students to whom we want to send email.
    :param param_dict: Parameters to pass to the email template.
    """
    for student in students:
        param_dict['full_name'] = student.profile.name
        message = ChangesEmail().personalize(
            recipient=Recipient(username='', email_address=student.email),
            language='en',
            user_context=param_dict,
        )

        try:
            TASK_LOG.info(u'Attempting to send %s changes email to: %s, for course: %s',
                          param_dict['change_type'],
                          student.email,
                          param_dict['course_name'])
            ace.send(message)
            TASK_LOG.info(u'Success: Task sending email for %s change to: %s , For course: %s',
                          param_dict['change_type'],
                          student.email,
                          param_dict['course_name'])
        except:
            TASK_LOG.info(u'Failure: Task sending email for %s change to: %s , For course: %s',
                          param_dict['change_type'],
                          student.email,
                          param_dict['course_name'])


def get_course_enrollments(course_id):
    """
    This function will get all of the students enrolled in the specific course.

    :param course_id: id of the specific course.
    :return: List of the enrolled students.
    """
    course_enrollments = CourseEnrollment.objects.filter(course_id=course_id)
    students = [enrollment.user for enrollment in course_enrollments]
    return students


@task(bind=True)
def send_course_enrollment_mail(user_email, email_params):
    try:
        TASK_LOG.info(u'Attempting to send course enrollment email to: %s, for course: %s',
                      user_email, email_params['course_name'])
        send_mail_to_student(user_email, email_params)
        TASK_LOG.info(u'Success: Task sending email to: %s , For course: %s',
                      user_email, email_params['course_name'])
    except:
        TASK_LOG.info(u'Failure: Task sending email tos: %s , For course: %s',
                      user_email, email_params['course_name'])
