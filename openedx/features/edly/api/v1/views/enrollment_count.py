from opaque_keys.edx.keys import CourseKey
from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from openedx.core.djangoapps.catalog.utils import get_programs
from openedx.features.edly.api.v1.views.utils import error_response
from openedx.features.edly.permissions import IsWpAdminUser
from openedx.features.edly.utils import (
    get_enrolled_learners_count,
    get_program_course_run_ids,
    is_course_org_same_as_site_org
)


class EdlyProgramEnrollmentCountViewSet(viewsets.ViewSet):
    """
    **Use Case**

        Get the number of enrollments for a program.

    **Example Request**

        GET /api/v1/programs/enrollment_count/{program_uuid}

    **GET Parameters**

        * program_uuid: The UUID of the program.

    **Response Values**

        If the request is successful, the request returns an HTTP 200 "OK" response.

        The HTTP 200 response has the following values.

        * enrolled_learners_count: The number of enrollments for the program.
    """
    permission_classes = (IsAuthenticated, IsWpAdminUser)

    def retrieve(self, request, pk=None):
        """
        Get the number of enrolled learners in a given program.
        """
        program = get_programs(uuid=pk)
        if not program:
            return error_response('Program not found.', status.HTTP_404_NOT_FOUND)

        course_run_ids = get_program_course_run_ids(program)

        if not course_run_ids:
            return Response({'enrolled_learners_count': 0}, status=status.HTTP_200_OK)

        course = CourseKey.from_string(course_run_ids[0])

        if not is_course_org_same_as_site_org(request.site, course):
            return error_response(
                'Program is not in the same organization as the site.',
                status.HTTP_403_FORBIDDEN
            )

        return Response(
            {'enrolled_learners_count': get_enrolled_learners_count(course_run_ids)},
            status=status.HTTP_200_OK
        )
