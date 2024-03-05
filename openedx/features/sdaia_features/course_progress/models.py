"""
Models
"""
from django.contrib.auth.models import User  # lint-amnesty, pylint: disable=imported-auth-user
from django.db import models

from opaque_keys.edx.django.models import CourseKeyField


class CourseCompletionEmailHistory(models.Model):
    """
    Keeps progress for a student for which he/she gets an email as he/she reaches at that particluar progress in a course.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    course_key = CourseKeyField(max_length=255, db_index=True)
    last_progress_email_sent = models.IntegerField(default=0)
