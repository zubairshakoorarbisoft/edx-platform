from rest_framework import serializers

from lms.djangoapps.certificates.models import GeneratedCertificate

from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from openedx.core.djangoapps.enrollments.serializers import CourseSerializer
from openedx.core.djangoapps.user_api.serializers import UserSerializer

class GeneratedCertificateSerializer(serializers.ModelSerializer):
    """Serializers have an abstract create & update, but we often don't need them. So this silences the linter."""

    course_info = serializers.SerializerMethodField()
    user = UserSerializer()

    def get_course_info(self, obj):
        try:
            self._course_overview = CourseOverview.get_from_id(obj.course_id)
            if self._course_overview:
                self._course_overview = CourseSerializer(self._course_overview).data
        except (CourseOverview.DoesNotExist, OSError):
            self._course_overview = None
        return self._course_overview


    class Meta:
        model = GeneratedCertificate
        fields = ('user', 'course_id', 'created_date', 'grade', 'key', 'status', 'mode', 'name', 'course_info')
