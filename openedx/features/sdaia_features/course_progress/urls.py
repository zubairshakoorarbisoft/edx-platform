"""
URLs for User Watch Hours - SDAIA Specific.
"""

from django.urls import path  # pylint: disable=unused-import
from django.conf.urls import include


urlpatterns = [
    path(
        "/api/v1/",
        include("openedx.features.sdaia_features.course_progress.api.v1.urls", namespace="course_progress_api_v1"),
    ),
]
