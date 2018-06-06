# -*- coding: utf-8 -*-
"""
Serializers for enterprise api version 1.
"""
from __future__ import absolute_import, unicode_literals

from rest_framework import serializers
from openedx.core.djangoapps.assignments import models
from openedx.core.lib.api.serializers import CourseKeyField


class CourseRunAssignmentSerializer(serializers.ModelSerializer):
    course_run_id = CourseKeyField()

    class Meta:
        model = models.CourseRunAssignment
        fields = '__all__'
        read_only_fields = (
            'course_run_id',
            'block_id',
            'display_name',
            'due_date'
        )
