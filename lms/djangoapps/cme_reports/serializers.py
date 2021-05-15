from rest_framework import serializers
from student.models import CourseEnrollment
from common.djangoapps.course_category.models import CourseCategory
from course_modes.models import CourseMode
from lms.djangoapps.certificates.models import GeneratedCertificate


class CourseListSerializer(serializers.ModelSerializer):
    course_display_name = serializers.SerializerMethodField()
    enrollment_count = serializers.SerializerMethodField()
    category = serializers.SerializerMethodField()

    class Meta:
        model = CourseMode
        fields = "__all__"

    def get_course_display_name(self, obj):
        return obj.course.display_name

    def get_enrollment_count(self, obj):
        enrollment_count = CourseEnrollment.objects.filter(course_id=obj.course, mode=obj.mode_slug).count()
        return enrollment_count

    def get_category(self, obj):
        try:
            categories_list = CourseCategory.get_course_category(obj.course.id).values_list('name', flat=True)
        except:
            categories_list = []
        return ', '.join(categories_list)


class CourseCertificateSerializers(serializers.ModelSerializer):
    user_fullname = serializers.SerializerMethodField()
    user_email = serializers.SerializerMethodField()
    user_npi = serializers.SerializerMethodField()
    user_state = serializers.SerializerMethodField()
    user_city = serializers.SerializerMethodField()
    created_date = serializers.SerializerMethodField()

    class Meta:
        model = GeneratedCertificate
        fields = '__all__'

    def get_user_fullname(self, obj):
        return obj.user.profile.name

    def get_user_email(self, obj):
        return obj.user.email

    def get_user_npi(self, obj):
        return obj.user.profile.npi or '--'

    def get_user_state(self, obj):
        return obj.user.profile.get_state_display() or '--'

    def get_user_city(self, obj):
        return obj.user.profile.city or '--'

    def get_created_date(self, obj):
        return obj.created_date.strftime("%d-%b-%Y")

