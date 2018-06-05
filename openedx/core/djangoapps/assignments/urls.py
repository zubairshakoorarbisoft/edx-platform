# -*- coding: utf-8 -*-
"""
URL definitions for assignments api endpoint.
"""
from __future__ import absolute_import, unicode_literals

from rest_framework.routers import DefaultRouter
from django.conf.urls import include, url

from openedx.core.djangoapps.assignments import views

router = DefaultRouter()  # pylint: disable=invalid-name
router.register("assignments", views.CourseRunAssignmentViewSet, 'assignments')

urlpatterns = [
    url(r'^assignments/', include(router.urls), name='api')
]
