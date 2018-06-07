# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.utils.translation import ugettext_lazy as _
from django.apps import AppConfig


class AssignmentsConfig(AppConfig):
    name = 'openedx.core.djangoapps.assignments'
    verbose_name = _("Assignments")

    def ready(self):
        # Register the signals handled by assignments.
        from . import signals