# -*- coding: utf-8 -*-
"""
Views for assignments endpoint.
"""
from __future__ import absolute_import, unicode_literals

from logging import getLogger

from edx_rest_framework_extensions.authentication import BearerAuthentication, JwtAuthentication
from rest_framework import filters, permissions, viewsets
from rest_framework.authentication import SessionAuthentication
from student.models import CourseEnrollment
from django.contrib.auth.models import User
from openedx.core.djangoapps.assignments import serializers, models
from rest_framework.response import Response


LOGGER = getLogger(__name__)


class CourseRunAssignmentViewSet(viewsets.ViewSet):
    """

    """
    permission_classes = (permissions.IsAuthenticated,)
    authentication_classes = (JwtAuthentication, BearerAuthentication, SessionAuthentication,)

    def list(self, request):
        user = request.user
        # if request.GET.user_id:
        #     user = User.objects.get(id=request.GET.user_id)
        # if user != request.user and not request.user.is_staff:
        #     return
        enrollments = CourseEnrollment.objects.filter(user=user)
        assignments = models.CourseRunAssignment.objects.filter(
            course_run_id__in=[enrollment.course_id for enrollment in enrollments]
        )
        serializer = serializers.CourseRunAssignmentSerializer(assignments)
        return Response(serializer.data)