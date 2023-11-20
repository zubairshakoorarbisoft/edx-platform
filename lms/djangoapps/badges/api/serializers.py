"""
Serializers for Badges
"""


from rest_framework import serializers

from django.contrib.auth import get_user_model
from lms.djangoapps.badges.models import BadgeAssertion, BadgeClass, LeaderboardEntry
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
    profile_image_url = serializers.SerializerMethodField()

    def get_profile_image_url(self, instance):
        """
        Get the profile image URL for the given user instance.

        Args:
            instance: The instance of the model representing the user.

        Returns:
            str: The profile image URL.

        """
        return get_profile_image_urls_for_user(instance)['medium']
    
    class Meta:
        model = User
        fields = ('username', 'name', 'profile_image_url')


class UserLeaderboardSerializer(serializers.ModelSerializer):
    """
    Serializer for the BadgeAssertion model.
    """
    user = BadgeUserSerializer(read_only=True)

    class Meta:
        model = LeaderboardEntry
        fields = '__all__'
