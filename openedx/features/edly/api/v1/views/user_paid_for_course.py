from enum import Enum

from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from common.djangoapps.student.models import CourseEnrollment
from common.djangoapps.util.json_request import JsonResponse


class PaymentStatus(Enum):
    PAID = "paid"
    UNPAID = "unpaid"
    NOT_ENROLLED = "not_enrolled"
    ERROR = "error"


class UserPaidForCourseViewSet(viewsets.ViewSet):
    """
    **Use Case**

        Get the status of a user's paid status for a given course.

    **Example Request**

        GET /api/v1/user_paid_for_course/{course_id}

    **GET Parameters**

        * pk: The course id of the course to retrieve the user's paid status for.

    **Response Values**

        If the request is successful, the request returns an HTTP 200 "OK" response.

        The HTTP 200 response has the following values.

        * status: The status of the user's paid status for the course.
            Possible values are:
                * "paid": The user has paid for the course.
                * "unpaid": The user has not paid for the course.
                * "error": An error occurred while retrieving the user's paid status.
    """
    permission_classes = [IsAuthenticated]

    def retrieve(self, request, pk=None):
        try:
            course_key = CourseKey.from_string(pk)
            enrollment = CourseEnrollment.get_enrollment(request.user, course_key)
            if not enrollment:
                return JsonResponse({"status": PaymentStatus.NOT_ENROLLED.value}, status=200)

            order_exists = enrollment.get_order_attribute_value('order_number')
            payment_status = PaymentStatus.PAID if order_exists else PaymentStatus.UNPAID

            return JsonResponse({"status": payment_status.value}, status=200)

        except (InvalidKeyError, Exception):
            return JsonResponse({"status": PaymentStatus.ERROR.value}, status=406)
