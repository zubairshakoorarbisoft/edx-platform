"""
URLs for user v1 API
"""

from django.conf import settings
from django.conf.urls import url

from mobile_api.users.views import UserCourseStatus, UserDetail
from mobile_api.v1.users.views import UserCourseEnrollmentsList

urlpatterns = [
    url('^' + settings.USERNAME_PATTERN + '$', UserDetail.as_view(), name='user-detail'),
    url(
        '^' + settings.USERNAME_PATTERN + '/course_enrollments/$',
        UserCourseEnrollmentsList.as_view(),
        name='courseenrollment-detail'
    ),
    url('^{}/course_status_info/{}'.format(settings.USERNAME_PATTERN, settings.COURSE_ID_PATTERN),
        UserCourseStatus.as_view(),
        name='user-course-status')
]
