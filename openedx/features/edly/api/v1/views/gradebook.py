from django.db.models import Q

from lms.djangoapps.courseware.courses import get_course_by_id
from lms.djangoapps.grades.api import CourseGradeFactory
from lms.djangoapps.grades.course_data import CourseData
from lms.djangoapps.grades.rest_api.v1.gradebook_views import (
    GradebookView,
    bulk_gradebook_view_context,
    course_author_access_required,
    verify_writable_gradebook_enabled
)
from openedx.core.lib.api.view_utils import verify_course_exists


class GradebookAPI(GradebookView):
    """
    **Use Case**

        Get the paginated gradebook for a specific course with optional search term filtering.

    **Example Request**

        GET /api/v1/gradebook/{course_id}/?user_contains={search_term}&page_size={page_size}

    **GET Parameters**

        * pk: The course id of the course to retrieve the gradebook for.
        * user_contains: The search term to filter the users by.
        * page_size: The number of results to return per page.
        * filtered_users

    **Response Values**

        If the request is successful, the request returns an HTTP 200 "OK" response that contains the following values:
        * results: A list of user enrollment objects as returned by `CourseGradeFactory`.
        * next: The URL to the next page of results.
        * previous: The URL to the previous page of results.

    """
    def _format_student_info(self, user, course_grade):
        """
        Formats the student information into a dictionary.
        """
        return {
            'username': user.username,
            'id': user.id,
            'email': user.email,
            'grade_summary': course_grade.summary
        }

    def _get_student_info(self, course_key, users):
        """
        Retrieves student information including grades for the given course.
        """
        student_info = []
        course = get_course_by_id(course_key, depth=None)
        course_data = CourseData(user=None, course=course)
        with bulk_gradebook_view_context(course_key, users):
            for user, course_grade, exc in CourseGradeFactory().iter(
                users, course_key=course_key, collected_block_structure=course_data.collected_structure
            ):
                if not exc:
                    student_info.append(self._format_student_info(user, course_grade))
        return student_info

    @verify_course_exists
    @verify_writable_gradebook_enabled
    @course_author_access_required
    def get(self, request, course_key):
        search_term = request.query_params.get('user_contains', '')

        q_objects = [
            Q(user__username__icontains=search_term) |
            Q(programcourseenrollment__program_enrollment__external_user_key__icontains=search_term) |
            Q(user__email__icontains=search_term)
        ]
        related_models = ['user']
        users = self._paginate_users(course_key, q_objects, related_models)

        student_info = self._get_student_info(course_key, users)
        users_counts = self._get_users_counts(course_key, q_objects)

        return self.get_paginated_response(student_info, **users_counts)
