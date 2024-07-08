"""
URLs for User Watch Hours - SDAIA Specific.
"""

from django.urls import path  # pylint: disable=unused-import
from .views import UserStatsAPIView


app_name = "nafath_api_v1"

urlpatterns = [
    path(r"user_stats", UserStatsAPIView.as_view()),
]
