"""
Utility functions for the course progress emails
"""

from lms.djangoapps.certificates.api import (
    certificates_viewable_for_course,
    get_certificates_for_user,
)
from lms.djangoapps.courseware.courses import get_course_blocks_completion_summary
from openedx.core.djangoapps.content.course_overviews.api import (
    get_course_overviews_from_ids,
    get_pseudo_course_overview,
)


def get_user_course_progress(user, course_key):
    """
    Function to get the user's course completion percentage in a course.
    :param user: The user object.
    :param course_key: The course key (e.g., CourseKey.from_string("edX/DemoX/Demo_Course")).
    :return: completion percentage.
    """
    completion_summary = get_course_blocks_completion_summary(course_key, user)

    complete_count = completion_summary.get("complete_count", 0)
    incomplete_count = completion_summary.get("incomplete_count", 0)
    locked_count = completion_summary.get("locked_count", 0)
    total_count = complete_count + incomplete_count + locked_count

    completion_percentage = round((complete_count / total_count) * 100)
    return completion_percentage


def get_user_certificates(username):
    user_certs = []
    for user_cert in _get_certificates_for_user(username):
        user_certs.append(
            {
                "username": user_cert.get("username"),
                "course_id": str(user_cert.get("course_key")),
                "course_display_name": user_cert.get("course_display_name"),
                "course_organization": user_cert.get("course_organization"),
                "certificate_type": user_cert.get("type"),
                "created_date": user_cert.get("created"),
                "modified_date": user_cert.get("modified"),
                "status": user_cert.get("status"),
                "is_passing": user_cert.get("is_passing"),
                "download_url": user_cert.get("download_url"),
                "grade": user_cert.get("grade"),
            }
        )
    return user_certs


def _get_certificates_for_user(username):
    """
    Returns a user's viewable certificates sorted by course name.
    """
    course_certificates = get_certificates_for_user(username)
    passing_certificates = {}
    for course_certificate in course_certificates:
        if course_certificate.get("is_passing", False):
            course_key = course_certificate["course_key"]
            passing_certificates[course_key] = course_certificate

    viewable_certificates = []
    course_ids = list(passing_certificates.keys())
    course_overviews = get_course_overviews_from_ids(course_ids)
    for course_key, course_overview in course_overviews.items():
        if not course_overview:
            # For deleted XML courses in which learners have a valid certificate.
            # i.e. MITx/7.00x/2013_Spring
            course_overview = get_pseudo_course_overview(course_key)
        if certificates_viewable_for_course(course_overview):
            course_certificate = passing_certificates[course_key]
            # add certificate into viewable certificate list only if it's a PDF certificate
            # or there is an active certificate configuration.
            if course_certificate["is_pdf_certificate"] or (
                course_overview and course_overview.has_any_active_web_certificate
            ):
                course_certificate["course_display_name"] = (
                    course_overview.display_name_with_default
                )
                course_certificate["course_organization"] = (
                    course_overview.display_org_with_default
                )
                viewable_certificates.append(course_certificate)

    viewable_certificates.sort(key=lambda certificate: certificate["created"])
    return viewable_certificates
