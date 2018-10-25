"""
Tests for users API
"""
from openedx.core.djangoapps.waffle_utils.testutils import override_waffle_flag
from openedx.features.course_duration_limits.config import CONTENT_TYPE_GATING_FLAG
from xmodule.modulestore.tests.factories import CourseFactory

from mobile_api.users.tests import TestUserEnrollmentApi as TestUserEnrollmentApiBase

@attr(shard=9)
@ddt.ddt
@override_settings(MKTG_URLS={'ROOT': 'dummy-root'})

class TestUserEnrollmentApi(TestUserEnrollmentApiBase):
    """
    Tests for /api/mobile/v0.5/users/<user_name>/course_enrollments/
    """
    REVERSE_INFO = {'name': 'courseenrollment-detail-v05', 'params': ['username']}
    LAST_YEAR = datetime.datetime.now(pytz.UTC) - datetime.timedelta(days=365)

    @override_waffle_flag(CONTENT_TYPE_GATING_FLAG, True)
    def test_expired_course_not_returned(self):
        self.login()
        # TODO - figure out correct way to create an expired course
        course = CourseFactory.create(start=self.LAST_YEAR, mobile_available=True)
        self.enroll(course.id)
        response = self.api_response()
        courses = response.data
        self.assertEqual(len(courses), 0)

    @override_waffle_flag(CONTENT_TYPE_GATING_FLAG, False)
    def test_expired_course_returned(self):
        self.login()
        # TODO - figure out correct way to create an expired course
        course = CourseFactory.create(start=self.LAST_YEAR, mobile_available=True)
        self.enroll(course.id)
        response = self.api_response()
        courses = response.data
        self.assertEqual(len(courses), 1)

