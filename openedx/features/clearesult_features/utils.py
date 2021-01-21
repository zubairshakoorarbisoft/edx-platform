"""
Helper functions for clearesult_features app.
"""
import io
import logging
import six
from csv import Error, DictReader, Sniffer
from datetime import datetime

from django.conf import settings
from django.contrib.sites.models import Site
from django.db.models import Sum, Case, When, IntegerField
from django.db.models.functions import Coalesce
from django.test import RequestFactory
from opaque_keys.edx.keys import CourseKey

from openedx.features.clearesult_features.models import (
    ClearesultUserProfile, ClearesultCourse,
    ClearesultGroupLinkage, ClearesultGroupLinkedCatalogs,
    ClearesultLocalAdmin, ClearesultCourseCompletion
)
from openedx.features.course_experience.utils import get_course_outline_block_tree

logger = logging.getLogger(__name__)


def get_file_encoding(file_path):
    """
    Returns the file encoding format.
    Arguments:
        file_path (str): Path of the file whose encoding format will be returned
    Returns:
        encoding (str): encoding format e.g: utf-8, utf-16, returns None if doesn't find
                        any encoding format
    """
    try:
        file = io.open(file_path, 'r', encoding='utf-8')
        encoding = None
        try:
            _ = file.read()
            encoding = 'utf-8'
        except UnicodeDecodeError:
            file.close()
            file = io.open(file_path, 'r', encoding='utf-16')
            try:
                _ = file.read()
                encoding = 'utf-16'
            except UnicodeDecodeError:
                logger.exception('The file encoding format must be utf-8 or utf-16.')

        file.close()
        return encoding

    except IOError as error:
        logger.exception('({}) --- {}'.format(error.filename, error.strerror))
        return None


def get_csv_file_control(file_path):
    """
    Returns opened file and dict_reader object of the given file path.
    """
    csv_file = None
    dialect = None
    try:
        encoding = get_file_encoding(file_path)
        if not encoding:
            logger.exception('Because of invlid file encoding format, user creation process is aborted.')
            return

        csv_file = io.open(file_path, 'r', encoding=encoding)
        try:
            dialect = Sniffer().sniff(csv_file.readline())
        except Error:
            logger.exception('Could not determine delimiter in the file.')
            csv_file.close()
            return

        csv_file.seek(0)
    except IOError as error:
        logger.exception('({}) --- {}'.format(error.filename, error.strerror))
        return

    dict_reader = DictReader(csv_file, delimiter=dialect.delimiter if dialect else ',')
    csv_reader = (dict((k.strip(), v.strip() if v else v) for k, v in row.items()) for row in dict_reader)

    return {'csv_file': csv_file, 'csv_reader': csv_reader}


def get_enrollments_and_completions(request, enrollments):
    """
    Returns user enrollment list for completed courses and incomplete courses
    and course completion dates as well.
    """
    complete_enrollments = []
    incomplete_enrollments = [enrollment for enrollment in enrollments]
    course_completions = {}
    for enrollment in enrollments:
        course_id_string = six.text_type(enrollment.course.id)
        course_outline_blocks = get_course_outline_block_tree(
            request, course_id_string, request.user
        )
        if course_outline_blocks:
            if course_outline_blocks.get('complete'):
                incomplete_enrollments.remove(enrollment)
                completion_date, pass_date = get_course_completion_and_pass_date(
                    enrollment.user, enrollment.course_id, is_graded=course_outline_blocks.get('graded')
                )
                course_completions[enrollment.id] = {
                        'completion_date': completion_date.date() if completion_date else None,
                        'pass_date': pass_date.date() if pass_date else None,
                }
                complete_enrollments.append(enrollment)

    return complete_enrollments, incomplete_enrollments, course_completions


def get_courses_progress(request, course_enrollments):
    """
    Gets course progress percentages of all courses in course_enrollments list

    :param request: request object
    :param course_enrollments: list of enrolled courses objects

    :return:
        courses_progress: progress percentage of each course in course_enrollments
    """
    courses_progress = []
    CORE_BLOCK_TYPES = getattr(settings, 'CORE_BLOCK_TYPES', [])
    FILTER_BLOCKS_IN_UNIT = getattr(settings, 'FILTER_BLOCKS_IN_UNIT', [])

    for enrollment in course_enrollments:
        course_id_string = six.text_type(enrollment.course.id)
        course_outline_blocks = get_course_outline_block_tree(
            request, course_id_string, request.user
        )

        total_blocks, total_completed_blocks = get_course_block_progress(
            course_outline_blocks,
            CORE_BLOCK_TYPES,
            FILTER_BLOCKS_IN_UNIT
        )

        course_progress = round((total_completed_blocks / total_blocks) * 100) if total_blocks else 0
        courses_progress.append(course_progress)

    return courses_progress


def get_course_block_progress(course_block, CORE_BLOCK_TYPES, FILTER_BLOCKS_IN_UNIT):
    """
    Recursive helper function to walk course tree outline,
    returning total core blocks and total completed core blocks

    This function does not filter progress of blocks in
    FILTER_BLOCK_IN_UNIT list if they are alone in a single unit

    :param course_block: root block object or child block
    :param CORE_BLOCK_TYPES: list of core block types from the settings
    :param FILTER_BLOCKS_IN_UNIT: list of core block types to filter in a unit

    :return:
        total_blocks: count of blocks in a root block block or child block
        total_completed_blocks: count of completed core blocks in a root block or child block
    """
    if course_block is None:
        return 0, 0

    course_block_children = course_block.get('children')
    block_type = course_block.get('type')

    if not course_block_children:
        if block_type in CORE_BLOCK_TYPES:
            if course_block.get('complete'):
                return 1, 1
            else:
                return 1, 0

        return 0, 0

    total_blocks = 0
    total_completed_blocks = 0
    is_multi_block_type = len(set([block.get('type') for block in course_block_children])) > 1
    is_block_vertical = block_type == 'vertical'

    for block in course_block_children:
        if (is_block_vertical and block.get('type') in FILTER_BLOCKS_IN_UNIT and is_multi_block_type):
            continue

        total_count, completed_count = get_course_block_progress(
            block,
            CORE_BLOCK_TYPES,
            FILTER_BLOCKS_IN_UNIT
        )

        total_blocks += total_count
        total_completed_blocks += completed_count

    return total_blocks, total_completed_blocks


def get_site_users(site):
    """
    Returns users list belong to site.
    """
    site_users = []
    site_name = "-".join(site.name.split('-')[:-1]).rstrip()

    # Note: site name must contain "-" otherwise it will return emty string.
    if not site_name:
        logger.info("Site name ({}) is not in a correct format.".format(site.name))
        logger.info("Correct format is <site_name> - <site_type> i.e. 'blackhills - LMS'.")
        return site_users

    clearesult_user_profiles = ClearesultUserProfile.objects.exclude(extensions={}).select_related("user")

    for profile in clearesult_user_profiles:
        user_site_identifiers =  profile.extensions.get('site_identifier', [])

        if site_name in user_site_identifiers:
            site_users.append(profile.user)

    return  site_users


def create_clearesult_course(destination_course_key, source_course_key=None, site=None):
    """
    Create a clearesult course instance for a new course or course rerun.

    If you call this function for a course rerun,
        source_course_key: will be the course key of the parent course.
        destination_course_key: will be the course key of actual course rerun.
        site: will be None and we will use the same site for rerun
              which we have used for parent course.

    If you call this function for a course,
        source_course_key: will be None
        destination_course_key: will be the actual course key which has been created.
        site: will be the domain of site which is being linked to the clearesult course.
              If you get `Public` for this then it means the clearesult course will be `Public`
              and we will save `None` for that
    """
    if site == 'Public':
        site = None
    elif site == None and source_course_key:
        site = ClearesultCourse.objects.get(course_id=source_course_key).site
    else:
        site = Site.objects.get(domain=site)

    ClearesultCourse.objects.create(course_id=destination_course_key, site=site)


def get_site_for_clearesult_course(course_id):
    """
    Return site if you find any site linked to the course.
    Return 'Public' if course is public.
    Return None if there is no relation of course with site has been saved.

    If course is not linked to a site, it means course is public.
    If course is linked to a site, it means course it is private.
    """
    try:
        site = ClearesultCourse.objects.get(course_id=course_id).site
        if site is None:
            site = 'Public'
            return site

        return site.domain
    except ClearesultCourse.DoesNotExist:
        return None


def is_compliant_with_clearesult_un_enroll_policy(enrollment):
    """
    Check that either user is compliant with clearesult un-enroll policy or not.
    Return False: if compliant
    Return True: if not compliant

    Un-enroll policy is:
        1. User can't un-enroll from paid courses for which he has enrolled
        2. User can't un-enroll from mandatory courses
    """
    clearesult_groups = ClearesultGroupLinkage.objects.filter(users__username=enrollment.user.username)
    clearesult_catalogs = ClearesultGroupLinkedCatalogs.objects.filter(group__in=clearesult_groups)
    for clearesult_catalog in clearesult_catalogs:
        if clearesult_catalog.mandatory_courses.filter(course_id=enrollment.course_id).exists():
            return False

    if not enrollment.mode in ['honor', 'audit']:
        return False

    return True


def is_local_admin_or_superuser(user):
    """
    If user is a local admin of any site or it's a superuser return True
    otherwise return False.
    """
    return user.is_superuser or ClearesultLocalAdmin.objects.filter(user=user).exists()


def get_course_completion_and_pass_date(user, course_id, is_graded):
    """
    Return course completion and pass date.

    The completion and pass date should be saved in ClearesultCourseCompletion
    according to the user enrollment. If it isn't, get the latest block completion
    date from BlockCompletion and save it.
    If course is not graded, completion date will be the pass date as well.

    Note: don't call this function if the course is not completed.
    """
    try:
        clearesult_course_completion = ClearesultCourseCompletion.objects.get(user=user, course_id=course_id)
    except ClearesultCourseCompletion.DoesNotExist:
        logger.info('Could not get completion for course {} and user {}'.format(course_id, user))
        return None, None

    return clearesult_course_completion.completion_date, clearesult_course_completion.pass_date


def generate_clearesult_course_completion(user, course_id):
    """
    On passing a course just set the pass date to the current date.
    """
    ClearesultCourseCompletion.objects.update_or_create(
        user=user, course_id=course_id,
        defaults={
            'pass_date': datetime.now()
        }
    )


def update_clearesult_course_completion(user, course_id):
    """
    This function will be called on course failure as it
    is associated with `COURSE_GRADE_NOW_FAILED` signal.

    So unless you pass a course for each step (attempting of problem)
    you will be considered as failed. Means this function will be called
    multiple times unlike `generate_clearesult_course_completion`

    In case of graded course and for failure just set the pass_date to None.
    For non graded course completion date will be the pass date.
    """
    is_graded = is_course_graded(course_id, user)
    clearesult_course_completion, created = ClearesultCourseCompletion.objects.get_or_create(
        user=user, course_id=course_id)

    if not created:
        if is_graded:
            clearesult_course_completion.pass_date = None
        else:
            clearesult_course_completion.pass_date = clearesult_course_completion.completion_date

        clearesult_course_completion.save()


def is_course_graded(course_id, user, request=None):
    """
    Check that course is graded.

    Arguments:
        course_id: (CourseKey/String) if CourseKey turn it into string
        request: (WSGI Request/None) if None create your own dummy request object

    Returns:
        is_graded (bool)
    """
    if request is None:
        request = RequestFactory().get(u'/')
        request.user = user

    if isinstance(course_id, CourseKey):
        course_id = six.text_type(course_id)

    course_outline = get_course_outline_block_tree(request, course_id, user)

    return course_outline.get('num_graded_problems') > 0
