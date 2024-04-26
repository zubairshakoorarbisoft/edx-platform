"""
URLs for badges API
"""
from django.conf import settings
from django.urls import re_path, path, include

from .views import UserBadgeAssertions, LeaderboardView, VerfyTokenView

from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'leaderboard', LeaderboardView, basename='leaderboard')

urlpatterns = [
    path('', include(router.urls)),
    re_path('^assertions/user/' + settings.USERNAME_PATTERN + '/$',
            UserBadgeAssertions.as_view(), name='user_assertions'),
    re_path('verify-lms-token/', VerfyTokenView.as_view(), name='verify-lms-token'),
]
