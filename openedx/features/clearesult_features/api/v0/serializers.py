"""
Serializers for Clearesult v0 APIs.
"""
import json

from django.contrib.sites.models import Site
from django.contrib.auth.models import User
from django.db.models import fields
from rest_framework.exceptions import NotFound
from rest_framework import serializers

from openedx.features.clearesult_features.models import (
    UserCreditsProfile, ClearesultCreditProvider, ClearesultCatalog,
    ClearesultCourse, ClearesultGroupLinkage
)
from openedx.features.clearesult_features.api.v0.validators import validate_user_for_site
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview


class UserCreditsProfileSerializer(serializers.ModelSerializer):
    credit_type_details = serializers.SerializerMethodField()

    def get_credit_type_details(self, obj):
        return {
            'name': obj.credit_type.name,
            'short_code': obj.credit_type.short_code,
        }

    class Meta:
        model = UserCreditsProfile
        fields = ('id', 'credit_type', 'credit_id', 'credit_type_details')
        read_only_fields = ('credit_type_details', 'id')
        write_only_fields = ('user',)


class ClearesultCreditProviderSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClearesultCreditProvider
        fields = ('short_code', 'name', 'id')
        read_only_fields = ('id', )


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('username', 'email', 'id')


class SiteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Site
        fields = ('id', 'domain')


class ClearesultGroupsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClearesultGroupLinkage
        fields = ('id', 'name', 'site', 'users')
        read_only_fields = ('id', )

    def validate_site(self, site):
        allowed_sites = self.context.get('allowed_sites')

        # for super user allowed sites will be null - no need to validate site
        if allowed_sites:
            if site not in allowed_sites:
                raise serializers.ValidationError(
                    u'You are not authorized to perform action on this site.'
                )
        return site

    def validate(self, validated_data):
        users = validated_data.get('users')
        if users:
            if self.instance:
                site = self.instance.site
            else:
                site = validated_data.get('site')

            if not site:
                raise serializers.ValidationError("Invalid action - for users, site is a required field")

            for user in users:
                if not (validate_user_for_site(user, site)):
                    raise serializers.ValidationError("Invalid action - users must belong to the site")
        return validated_data

    def to_representation(self, instance):
        response = super().to_representation(instance)
        response['site'] = SiteSerializer(instance.site).data
        response['users'] = UserSerializer(instance.users.all(), many=True).data
        return response


class ClearesultCourseSerializer(serializers.ModelSerializer):
    course_name = serializers.SerializerMethodField()
    site = SiteSerializer()
    class Meta:
        model = ClearesultCourse
        fields = '__all__'
        extra_kwargs = {'course_name': {'read_only': True}}

    def get_course_name(self, obj):
        try:
            display_name = CourseOverview.objects.get(id=obj.course_id).display_name
        except CourseOverview.DoesNotExist:
            raise NotFound('The course id: {} does not exist.'.format(obj.course_id))
        except AssertionError as err:
            raise NotFound(err)

        return display_name

class ClearesultCatalogSerializer(serializers.ModelSerializer):
    clearesult_courses = ClearesultCourseSerializer(many=True)
    site = SiteSerializer()
    class Meta:
        model = ClearesultCatalog
        fields = '__all__'
        read_only_fields = ('id', 'site',)
