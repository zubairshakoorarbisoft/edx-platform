"""
Serializers for Badges
"""


from rest_framework import serializers

from django.contrib.auth import get_user_model
from lms.djangoapps.badges.models import BadgeAssertion, BadgeClass
from openedx.core.djangoapps.user_api.accounts.image_helpers import get_profile_image_urls_for_user

User = get_user_model()

class BadgeClassSerializer(serializers.ModelSerializer):
    """
    Serializer for BadgeClass model.
    """
    image_url = serializers.ImageField(source='image')

    class Meta:
        model = BadgeClass
        fields = ('slug', 'issuing_component', 'display_name', 'course_id', 'description', 'criteria', 'image_url')


class BadgeAssertionSerializer(serializers.ModelSerializer):
    """
    Serializer for the BadgeAssertion model.
    """
    badge_class = BadgeClassSerializer(read_only=True)

    class Meta:
        model = BadgeAssertion
        fields = ('badge_class', 'image_url', 'assertion_url', 'created')


class BadgeUserSerializer(serializers.ModelSerializer):
    """
    Serializer for the BadgeAssertion model.
    """
    name = serializers.CharField(source='profile.name')

    class Meta:
        model = User
        fields = ('username', 'name')
    
    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['profile_image_url'] = get_profile_image_urls_for_user(instance)['medium']
        return data


class UserLeaderboardSerializer(serializers.Serializer):
    user = BadgeUserSerializer()
    badge_count = serializers.IntegerField()
    course_badge_count = serializers.IntegerField()
    event_badge_count = serializers.IntegerField()
    score = serializers.IntegerField()
    badges = BadgeAssertionSerializer(many=True)

    def to_representation(self, instance):
        data = super().to_representation(instance)
        return data

