import json

from django.http import HttpResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import parsers, permissions, status, viewsets
from edx_rest_framework_extensions.authentication import JwtAuthentication
from openedx.core.lib.api.authentication import (
    OAuth2AuthenticationAllowInactiveUser,
    SessionAuthenticationAllowInactiveUser
)
from .utils import get_json_entitlements_by_user
from .models import CourseEntitlement
from django.contrib.auth.models import User


# TODO Temp?
from django.core.context_processors import csrf
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie


from openedx.core.lib.api.permissions import ApiKeyHeaderPermission, ApiKeyHeaderPermissionIsAuthenticated


class EntitlementView(APIView):
    authentication_classes = (JwtAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, username):
        """
        TODO:
         - Add check to only return entitlements for a given user
        """
        return Response(get_json_entitlements_by_user(self, username))


class AddEntitlementView(APIView):
    authentication_classes = (JwtAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)

    @csrf_exempt
    def post(self, request):

        # TODO: Check the input data for Mode
        # TODO: Check to see if the Course Entitlement already exists for a user
        course_id = request.data.get('course_id', '')  # TODO: Replace test data
        expiration_date = request.data.get('expiration_date', '')  # '2017-09-14 11:47:58.000000'
        mode = request.data.get('mode', '')

        # TODO: Add actual user id retrieval
        # TODO: Add checking for the format of the course id and the expiration date format
        user = User.objects.get(id=6)
        new_entitlement = CourseEntitlement(user_id=user,
                                            root_course_id=course_id,
                                            enroll_end_date=expiration_date,
                                            mode=mode)
        new_entitlement.save()

        return Response('Success')

