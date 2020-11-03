"""
Auth pipeline to modify authentication behavior
"""
import logging

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.shortcuts import redirect
from social_django.models import UserSocialAuth

from third_party_auth import pipeline

from openedx.features.clearesult_features.auth_backend import ClearesultAzureADOAuth2

logger = logging.getLogger(__name__)
User = get_user_model()


def replace_old_clearesult_app_uid(backend, uid, details, response, *args, **kwargs):
    """
    When uid of the user social auth account available in edX and the user account coming from
    IdP doesn't match but they have same email address, get edX user account using email
    instead of uid and set it's uid value to the uid value that is coming from IdP so that
    both of these accounts are linked to each other.
    """
    if backend.name == ClearesultAzureADOAuth2.name:
        email = details.get('email').lower()
        if email:
            try:
                user = User.objects.get(email=email)
                social_auth_user = UserSocialAuth.objects.get(user=user, provider=backend.name)
                if social_auth_user.uid != uid:
                    logger.info('User with email {} is already linked.'.format(email))
                    social_auth_user.uid = uid
                    social_auth_user.save()
                    logger.info('User with email {} has been updated with new uid'.format(email))
            except (User.DoesNotExist, UserSocialAuth.DoesNotExist):
                logger.info('Could not find user or social_auth_user with email: {}.'.format(email))
        else:
            logger.info('Could not fetch email from facebook against uid: {}.'.format(uid))


def redirect_to_continuing_education(new_association, auth_entry, *_, **__):
    """
    Redirect a new registered user to "Continuing Education" page.
    """
    if new_association and auth_entry == pipeline.AUTH_ENTRY_REGISTER:
        return redirect(reverse('clearesult_features:continuing_education'))
