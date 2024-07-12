"""
The User Watch Hours API view - SDAIA Specific.
"""

import logging
import requests

from ccx_keys.locator import CCXLocator
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
from lms.djangoapps.program_enrollments.rest_api.v1.views import (
    UserProgramReadOnlyAccessView,
)
from openedx.core.djangoapps.catalog.utils import get_programs, get_programs_by_type
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

    @method_decorator(ensure_csrf_cookie_cross_domain)
    def get(self, request):
        """
        Gets the total watch hours for a user.
        """
        user = request.user
        user_id = user.id
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
        programs = []
        requested_program_type = "masters"
        if user.is_staff:
            programs = get_programs_by_type(request.site, requested_program_type)
        else:
            program_dict = {}
            # Check if the user is a course staff of any course which is a part of a program.
            programs_user_is_staff_for = (
                UserProgramReadOnlyAccessView().get_programs_user_is_course_staff_for(
                    user, requested_program_type
                )
            )
            for staff_program in programs_user_is_staff_for:
                program_dict.setdefault(staff_program["uuid"], staff_program)

            # Now get the program enrollments for user purely as a learner add to the list
            enrolled_programs = (
                UserProgramReadOnlyAccessView()._get_enrolled_programs_from_model(user)
            )
            for learner_program in enrolled_programs:
                program_dict.setdefault(learner_program["uuid"], learner_program)

            programs = list(program_dict.values())
        enrolled_programs = len(programs)

        ############ COURSES COUNT ############
        username = user.username
        try:
            enrolled_courses = len(get_course_enrollments(username))
        except CourseEnrollmentError:
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data={
                    "message": f"An error occurred while retrieving enrollments for user {username}"
                },
            )

        log.info(f'\n\n debugging start \n\n')
        site = request.site
        log.info(f'\n\n site: {site} \n\n')
        course_enrollments = list(get_course_enrollments(user.username))
        course_enrollments.sort(key=lambda x: x['created'], reverse=True)
        from openedx.core.djangoapps.programs.utils import ProgramProgressMeter
        meter = ProgramProgressMeter(site, user, enrollments=course_enrollments)

        inverted_programs = meter.invert_programs()
        log.info(f"\n\n\n meter.invert_programs() {inverted_programs}\n\n")
        engaged_programs = meter.engaged_programs()
        log.info(f"\n\n\n meter.engaged_programs() {engaged_programs}\n\n")

        ############ Response ############
        return Response(
            status=status.HTTP_200_OK,
            data={
                "inverted_programs": inverted_programs,
                "engaged_programs": engaged_programs,
                "watch_hours": watch_time,
                "enrolled_courses": enrolled_courses,
                "enrolled_programs": enrolled_programs,
            },
        )
