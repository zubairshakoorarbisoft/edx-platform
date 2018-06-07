"""
Signals for assignments.
"""
from importlib import import_module

from django.dispatch.dispatcher import receiver

from xmodule.modulestore.django import SignalHandler


@receiver(SignalHandler.course_published)
def trigger_update_course_assignment_dates(sender, course_key, **kwargs):  # pylint: disable=invalid-name,unused-argument
    """
    Trigger traverse_course() when course_published signal is fired.
    """
    tasks = import_module('openedx.core.djangoapps.assignments.tasks')
    tasks.update_course_assignment_dates.apply_async([unicode(course_key)], countdown=0)
