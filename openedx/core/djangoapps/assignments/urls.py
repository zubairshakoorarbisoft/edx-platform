# -*- coding: utf-8 -*-
from django.conf.urls import url

from .views import CourseRunAssignmentViewSet


urlpatterns = [
    url(r'^v1/assignments/', CourseRunAssignmentViewSet.as_view({'get': 'list'}), name='assignments')
]
