import logging
import re

from django.conf import settings

from contentstore.utils import get_lms_link_for_item, is_currently_visible_to_students
from courseware.courses import get_course_by_id
from static_replace import replace_static_urls
from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers
from openedx.core.djangoapps.theming.helpers import get_current_site
from openedx.features.edly.tasks import send_bulk_mail_to_students
from student.models import CourseEnrollment

log = logging.getLogger(__name__)

COURSE_OUTLINE_CATEGORIES = ['vertical', 'sequential', 'chapter']


def notify_students_about_xblock_changes(xblock, publish, old_content):
    """
    This function is responsible for calling the related function by checking the xblock category.

    Arguments:
        xblock: Block of courses which has been published.
        publish: Param to check if xblock is going to be published.
        old_content: Old data of xblock before updating.
    """
    if (publish == 'make_public' and xblock.category in COURSE_OUTLINE_CATEGORIES
            and is_currently_visible_to_students(xblock)):
        _handle_section_publish(xblock)
    elif xblock.category == 'course_info' and xblock.location.block_id == 'handouts':
        _handle_handout_changes(xblock, old_content)


def get_email_params(xblock):
    """
    Generates the email params for any changes in course

    Arguments:
        xblock: xblock which is modified/created

    Returns:
        Dict containing the data for email.
    """
    email_params = {}
    course = get_course_by_id(xblock.location.course_key)
    email_params['site'] = get_current_site()
    email_params['course_url'] = _get_course_url(xblock.location.course_key)
    email_params['course_name'] = course.display_name_with_default
    email_params['display_name'] = xblock.display_name
    email_params['platform_name'] = settings.PLATFORM_NAME
    email_params['site_name'] = configuration_helpers.get_value(
        'SITE_NAME',
        settings.SITE_NAME
    )
    return email_params


def _get_course_url(course_key):
    return '{}/courses/{}'.format(settings.LMS_ROOT_URL, course_key)


def _handle_section_publish(xblock):
    """
    This function will send email to the enrolled students in the case
    of any outline changes like section, subsection, unit publish.

    Arguments:
        xblock: xblock which is modified/created
    """

    email_params = get_email_params(xblock)
    students = get_course_enrollments(xblock.location.course_key)
    email_params['change_url'] = get_lms_link_for_item(xblock.location).strip('//')
    if xblock.category == 'vertical':
        email_params['change_type'] = 'Unit'
    elif xblock.category == 'sequential':
        email_params['change_type'] = 'Sub Section'
    else:
        email_params['change_type'] = 'Section'

    send_bulk_mail_to_students.delay(students, email_params, 'outline_changes')


def _handle_handout_changes(xblock, old_content):
    """
    This function is responsible for generating email data for any type of handout changes and will send the email to
    enrolled students.

    Arguments:
        xblock: Update handouts xblock
        old_content: Old content of the handout xblock
    """
    # Operations for New Xblock Data
    new_content_with_replaced_static_urls = replace_static_urls(xblock.data, course_id=xblock.location.course_key)
    absolute_urls_of_new_data = _get_urls(new_content_with_replaced_static_urls)
    new_content_with_absolute_urls = _replace_relative_urls_with_absolute_urls(
        new_content_with_replaced_static_urls,
        absolute_urls_of_new_data)

    # Operations for old xblock data
    old_content_with_replaced_static_urls = replace_static_urls(
        old_content.get('data'),
        course_id=xblock.location.course_key)
    absolute_urls_of_old_data = _get_urls(old_content_with_replaced_static_urls)
    old_content_with_absolute_urls = _replace_relative_urls_with_absolute_urls(
        old_content_with_replaced_static_urls,
        absolute_urls_of_old_data)

    email_params = get_email_params(xblock)
    email_params['old_content'] = old_content_with_absolute_urls
    email_params['new_content'] = new_content_with_absolute_urls
    students = get_course_enrollments(xblock.location.course_key)
    send_bulk_mail_to_students.delay(students, email_params, 'handout_changes')


def _replace_relative_urls_with_absolute_urls(content, absolute_urls):
    """
    This function will replace the all relative url from the given content to the absolute urls

    Arguments:
        content: Content to be changed
        relative_urls: List of relative urls to change from content
        absolute_urls: List of absolute urls to change with relative urls.

    Returns:
        Updated content contains all absolute urls.
    """
    for relative_url, absolute_url in absolute_urls.items():
        content = content.replace(relative_url, absolute_url)
    return content


def _get_urls(content):
    """
    This function will extract the relative urls from content

    Arguments:
        content: String from which we have to extract the relative imports

    Returns:
        List of relative urls
    """
    absolute_urls = {}
    pattern = r'href' '*=' '*("/asset[:.A-z0-9/+@-]*")'
    try:
        relative_urls = re.findall(pattern, content)
        for relative_url in relative_urls:
            absolute_urls[relative_url] = '"{}{}"'.format(
                                                        settings.LMS_ROOT_URL,
                                                        relative_url.replace('"', ''))
    except TypeError:
        # If new course created the old_content will be None or Empty
        return {}
    return absolute_urls


def get_course_enrollments(course_id):
    """
    This function will get all of the students enrolled in the specific course.

    Arguments:
        course_id: id of the specific course.
    Returns:
        List of the enrolled students.
    """
    course_enrollments = CourseEnrollment.objects.filter(course_id=course_id, is_active=True)
    students = [enrollment.user for enrollment in course_enrollments]
    return students
