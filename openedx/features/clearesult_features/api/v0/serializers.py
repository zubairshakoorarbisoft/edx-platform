"""
Serializers for Clearesult v0 APIs.
"""
from django.contrib.sites.models import Site
from django.db.models import fields
from rest_framework.exceptions import NotFound
from rest_framework import serializers

import json

from openedx.features.clearesult_features.models import (
    UserCreditsProfile, ClearesultCreditProvider, ClearesultCatalog,
    ClearesultCourse
)
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


class SiteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Site
        fields = ('id', 'domain')

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
