"""
Tests for coursegraph's signal handler on course publish
"""
from __future__ import unicode_literals

import mock

from opaque_keys.edx.keys import CourseKey

from openedx.core.djangoapps.coursegraph.signals import _listen_for_course_publish
from django.test import TestCase


class TestCourseGraphSignalHandler(TestCase):
    """
    Tests for the course publish signal handler
    """
    @mock.patch("openedx.core.djangoapps.coursegraph.signals.ModuleStoreSerializer")
    def test_neo4j_updated_on_course_publish(self, mock_mss_class):
        """
        Tests that neo4j is updated on course publish
        """
        course_key = CourseKey.from_string('course-v1:org+course+run')
        mock_mss = mock_mss_class.return_value
        _listen_for_course_publish(None, course_key)
        mock_mss.dump_course_to_neo4j.assertCalled_once_with(course_key)
