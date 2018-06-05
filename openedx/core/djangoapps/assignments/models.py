# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models


class CourseRunAssignment(models.Model):
    """
    CourseRunAssignment model.
    """
    course_run_id = models.CharField(max_length=100, null=False, blank=False)
    sequential_id = models.CharField(max_length=100, null=False, blank=False)
    sequential_name = models.CharField(max_length=255, null=False, blank=False)
    due_date = models.DateTimeField(auto_now_add=True)

    class Meta(object):
        """
        CourseRunAssignment metadata.
        """
        unique_together = ('course_run_id', 'sequential_id')

    def __unicode__(self):
        return self.sequential_name
