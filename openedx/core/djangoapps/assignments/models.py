# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models


class CourseRunAssignment(models.Model):
    """
    CourseRunAssignment model.
    """
    course_run_id = models.CharField(max_length=100, null=False, blank=False)
    block_id = models.CharField(max_length=100, null=False, blank=False)
    display_name = models.CharField(max_length=255, null=False, blank=False)
    due_date = models.DateTimeField(null=True, blank=True)

    class Meta(object):
        """
        CourseRunAssignment metadata.
        """
        unique_together = ('course_run_id', 'block_id')

    def __unicode__(self):
        return self.display_name
