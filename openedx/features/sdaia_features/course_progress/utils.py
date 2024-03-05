"""
Utility functions for the course progress emails
"""
from lms.djangoapps.courseware.courses import get_course_blocks_completion_summary


def get_user_course_progress(user, course_key):
    """
    Function to get the user's course completion percentage in a course.
    :param user: The user object.
    :param course_key: The course key (e.g., CourseKey.from_string("edX/DemoX/Demo_Course")).
    :return: completion percentage.
    """
    completion_summary = get_course_blocks_completion_summary(course_key, user)

    complete_count = completion_summary.get('complete_count', 0)
    incomplete_count = completion_summary.get('incomplete_count', 0)
    locked_count = completion_summary.get('locked_count', 0)
    total_count = complete_count + incomplete_count + locked_count

    completion_percentage = (complete_count / total_count) * 100
    return completion_percentage