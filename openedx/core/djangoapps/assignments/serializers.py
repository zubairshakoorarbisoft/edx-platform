# -*- coding: utf-8 -*-
"""
Serializers for enterprise api version 1.
"""
from __future__ import absolute_import, unicode_literals

from rest_framework import serializers
from openedx.core.djangoapps.assignments import models


class CourseRunAssignmentSerializer(serializers.Serializer):
    """

    """
    class Meta:
        model = models.CourseRunAssignment
        fields = ()
