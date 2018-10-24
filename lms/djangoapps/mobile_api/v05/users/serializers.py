"""
Serializer for user v0.5 API
"""
from mobile_api.users.serializers import CourseEnrollmentSerializer as CourseEnrollmentSerializerBase
from student.models import CourseEnrollment


class CourseEnrollmentSerializer(CourseEnrollmentSerializerBase):
    """
    Serializes CourseEnrollment models for v0.5 api
    Does not include 'expiration' field that is present in v1 api
    """
    class Meta(object):
        model = CourseEnrollment
        fields = ('created', 'mode', 'is_active', 'course', 'certificate')
        lookup_field = 'username'
