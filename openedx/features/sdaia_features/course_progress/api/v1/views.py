"""
The User Watch Hours API view - SDAIA Specific.
"""

import logging
import requests

from django.conf import settings
from django.utils.decorators import method_decorator
from edx_rest_framework_extensions.auth.jwt.authentication import JwtAuthentication
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from common.djangoapps.student.roles import (
    CourseInstructorRole,
    CourseStaffRole,
    UserBasedRole,
)
from common.djangoapps.util.disable_rate_limit import can_disable_rate_limit
from lms.djangoapps.program_enrollments.api import fetch_program_enrollments_by_student
from lms.djangoapps.program_enrollments.constants import ProgramEnrollmentStatuses
from openedx.core.djangoapps.catalog.utils import get_programs
from openedx.core.djangoapps.cors_csrf.decorators import ensure_csrf_cookie_cross_domain
from openedx.core.djangoapps.enrollments.errors import CourseEnrollmentError
from openedx.core.djangoapps.enrollments.data import get_course_enrollments
from openedx.core.djangoapps.enrollments.views import EnrollmentCrossDomainSessionAuth
from openedx.core.lib.api.authentication import BearerAuthenticationAllowInactiveUser
from openedx.core.lib.api.permissions import ApiKeyHeaderPermissionIsAuthenticated


log = logging.getLogger(__name__)


@can_disable_rate_limit
class UserStatsAPIView(APIView):
    """
    APIView to get the total watch hours for a user.

    **Example Requests**
        GET /sdaia/api/v1/user_stats

        It return watch_time in hours
        Response: {
            "watch_hours": 0.00043390860160191856,
            "enrolled_courses": enrolled_courses,
            "enrolled_programs": enrolled_programs,
        }
    """

    authentication_classes = (
        JwtAuthentication,
        BearerAuthenticationAllowInactiveUser,
        EnrollmentCrossDomainSessionAuth,
    )
    permission_classes = (ApiKeyHeaderPermissionIsAuthenticated,)

    def get_program_uuids_user_is_course_staff_for(self, user, program_type_filter):
        """
        Return a list of programs the user is course staff for.
        This function would take a list of course runs the user is staff of, and then
        try to get the Masters program associated with each course_runs.
        """
        program_uuids = []
        for course_key in self.get_course_keys_user_is_staff_for(user):
            course_run_programs = get_programs(course=course_key)
            for course_run_program in course_run_programs:
                if (
                    course_run_program
                    and course_run_program.get("type").lower() == program_type_filter
                ):
                    program_uuids.append(course_run_program["uuid"])

        return program_uuids

    def get_course_keys_user_is_staff_for(self, user):
        """
        Return all the course keys the user is course instructor or course staff role for
        """

        # Get all the courses of which the user is course staff for. If None, return false
        def filter_ccx(course_access):
            """CCXs cannot be edited in Studio and should not be filtered"""
            return not isinstance(course_access.course_id, CCXLocator)

        instructor_courses = UserBasedRole(
            user, CourseInstructorRole.ROLE
        ).courses_with_role()
        staff_courses = UserBasedRole(user, CourseStaffRole.ROLE).courses_with_role()
        all_courses = list(filter(filter_ccx, instructor_courses | staff_courses))
        course_keys = {}
        for course_access in all_courses:
            if course_access.course_id is not None:
                course_keys[course_access.course_id] = course_access.course_id

        return list(course_keys.values())

    def _get_enrolled_programs_from_model(self, user):
        """
        Return the Program Enrollments linked to the learner within the data model.
        """
        program_enrollments = fetch_program_enrollments_by_student(
            user=user,
            program_enrollment_statuses=ProgramEnrollmentStatuses.__ACTIVE__,
        )
        uuids = [enrollment.program_uuid for enrollment in program_enrollments]
        return get_programs(uuids=uuids) or []

    @method_decorator(ensure_csrf_cookie_cross_domain)
    def get(self, request):
        """
        Gets the total watch hours for a user.
        """
        user_id = request.user.id
        username = request.user.username
        clickhouse_uri = (
            f"{settings.CAIRN_CLICKHOUSE_HTTP_SCHEME}://{settings.CAIRN_CLICKHOUSE_USERNAME}:{settings.CAIRN_CLICKHOUSE_PASSWORD}@"
            f"{settings.CAIRN_CLICKHOUSE_HOST}:{settings.CAIRN_CLICKHOUSE_HTTP_PORT}/?database={settings.CAIRN_CLICKHOUSE_DATABASE}"
        )
        query = f"SELECT SUM(duration) as `Watch time` FROM `openedx`.`video_view_segments` WHERE user_id={user_id};"

        ############ WATCH HOURS ############
        try:
            response = requests.get(clickhouse_uri, data=query.encode("utf8"))
            watch_time = float(response.content.decode().strip()) / (60 * 60)
        except Exception as e:
            log.error(
                f"Unable to fetch watch for user {user_id} due to this exception: {str(e)}"
            )
            raise HTTPException(status_code=500, detail=str(e))

        ############ PROGRAMS COUNT ############
        program_uuids = []
        # Check if the user is a course staff of any course which is a part of a program.
        requested_program_type = "masters"
        for staff_program_uuid in self.get_program_uuids_user_is_course_staff_for(
            request_user, requested_program_type
        ):
            program_uuids.append(staff_program_uuid)

        # Now get the program enrollments for user purely as a learner add to the list
        for learner_program in self._get_enrolled_programs_from_model(request_user):
            program_uuids.append(learner_program["uuid"])

        # unique UUIDs count
        enrolled_programs = len(list(set(program_uuids)))

        ############ COURSES COUNT ############
        try:
            enrolled_courses = len(get_course_enrollments(username))
        except CourseEnrollmentError:
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data={
                    "message": f"An error occurred while retrieving enrollments for user {username}"
                },
            )

        ############ Response ############
        return Response(
            status=status.HTTP_200_OK,
            data={
                "watch_hours": watch_time,
                "enrolled_courses": enrolled_courses,
                "enrolled_programs": enrolled_programs,
            },
        )
