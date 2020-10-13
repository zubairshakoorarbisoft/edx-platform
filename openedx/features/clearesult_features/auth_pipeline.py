import logging

from django.contrib.auth import get_user_model
from social_django.models import UserSocialAuth

from openedx.features.clearesult_features.auth_backend import ClearesultAzureADOAuth2

logger = logging.getLogger(__name__)
User = get_user_model()


def replace_old_clearesult_app_uid(backend, uid, details, response, *args, **kwargs):
    """
    When uid of the user social auth account available in edX, just get that account using the
    email coming from IdP and then set it's uid according to the uid coming from IdP.
    """
    if backend.name == ClearesultAzureADOAuth2.name:
        email = details.get('email')
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
