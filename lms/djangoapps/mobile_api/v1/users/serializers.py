"""
Serializer for user v1 API
"""

from rest_framework import serializers
from mobile_api.users.serializers import CourseEnrollmentSerializer as CourseEnrollmentSerializerBase
from openedx.features.course_duration_limits.access import get_user_course_expiration_date
from student.models import CourseEnrollment


class CourseEnrollmentSerializer(CourseEnrollmentSerializerBase):
    """
    Extend base CourseEnrollmentSerializer, add expiration field
    """
    expiration = serializers.SerializerMethodField()

    def get_expiration(self, model):
        """
        Returns expiration date for a course, if any or null
        """
        return get_user_course_expiration_date(model.user, model.course)

    class Meta(object):
        model = CourseEnrollment
        fields = ('expiration', 'created', 'mode', 'is_active', 'course', 'certificate')
        lookup_field = 'username'
