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


class EntitlementView(APIView):
    authentication_classes = (JwtAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request):
        """
        TODO:
         - Add check to only return entitlements for a given user
        """
        return Response(get_json_entitlements_by_user(self, request.query_params.get('username', '')))

    @csrf_exempt
    def put(self, request):

        # TODO: Check the input data for Mode
        # TODO: Check to see if the Course Entitlement already exists for a user
        course_entitlement_details = request.data.get('course_entitlement_details', {})  # TODO: Replace test data
        course_id = course_entitlement_details.get('course_id', '')
        expiration_date = request.data.get('expiration_date', '')  # '2017-09-14 11:47:58.000000'
        mode = request.data.get('mode', '')
        username = request.data.get('user', '')
        is_active = request.data.get('is_active', False)

        # TODO: Add actual user id retrieval
        # TODO: Add checking for the format of the course id and the expiration date format
        user = User.objects.get(username=username)
        entitlement_data = {
            'user_id': user,
            'root_course_id': course_id,
            'enroll_end_date': expiration_date,
            'mode': mode,
            'is_active': is_active
        }
        stored_entitlement, is_created = CourseEntitlement.objects.update_or_create(
            user_id=user,
            root_course_id=course_id,
            defaults=entitlement_data
        )

        if is_created:
            return Response('New entitlement created')
        else:
            return Response('Updated existing entitlement')

