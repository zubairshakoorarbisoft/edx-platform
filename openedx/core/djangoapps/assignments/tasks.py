"""
Tasks for assignments.
"""
import logging

from celery.task import task  # pylint: disable=import-error,no-name-in-module
from opaque_keys.edx.keys import CourseKey
from opaque_keys.edx.locator import CourseLocator

from xmodule.modulestore.django import modulestore

log = logging.getLogger('edx.celery.task')


@task(name=u'openedx.core.djangoapps.assignments.tasks.traverse_course')
def traverse_course(course_id):
    """
    Find all subsections (sequential blocks) for a given course.

    TESTING: traverse_course(u'course-v1:edX+DemoX+Demo_Course')

    Arguments:
        course_id (String|CourseLocator): The course_id of a course.
    """
    if isinstance(course_id, basestring):
        course_id_string = course_id
    elif isinstance(course_id, CourseLocator):
        course_id_string = unicode(course_id)
    else:
        raise ValueError('course_id must be a string or a CourseLocator. ' 
                         '{} is not acceptable.'.format(type(course_id)))

    course_key = CourseKey.from_string(course_id_string)
    seq_xblocks = modulestore().get_items(
        course_key,
        qualifiers={'category': 'sequential'},
        include_orphans=False)

    for xblock in seq_xblocks:
        print xblock.due
