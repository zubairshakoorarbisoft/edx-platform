"""
Utility functions for third_party_auth
"""

from uuid import UUID
from django.contrib.auth.models import User

from .models import _PSA_OAUTH2_BACKENDS, OAuth2ProviderConfig


def user_exists(details):
    """
    Return True if user with given details exist in the system.

    Arguments:
        details (dict): dictionary containing user infor like email, username etc.

    Returns:
        (bool): True if user with given details exists, `False` otherwise.
    """
    user_queryset_filter = {}
    email = details.get('email')
    username = details.get('username')
    if email:
        user_queryset_filter['email'] = email
    elif username:
        user_queryset_filter['username__iexact'] = username

    if user_queryset_filter:
        return User.objects.filter(**user_queryset_filter).exists()

    return False


def convert_saml_slug_provider_id(provider):
    """
    Provider id is stored with the backend type prefixed to it (ie "saml-")
    Slug is stored without this prefix.
    This just converts between them whenever you expect the opposite of what you currently have.

    Arguments:
        provider (string): provider_id or slug

    Returns:
        (string): Opposite of what you inputted (slug -> provider_id; provider_id -> slug)
    """
    if provider.startswith('saml-'):
        return provider[5:]
    else:
        return 'saml-' + provider


def validate_uuid4_string(uuid_string):
    """
    Returns True if valid uuid4 string, or False
    """
    try:
        UUID(uuid_string, version=4)
    except ValueError:
        return False
    return True


def get_enabled_oauth_providers():
    """
    Helper method that returns a list of Oauth2 providers of the current site.
    """
    providers = []
    oauth2_slugs = OAuth2ProviderConfig.key_values('slug', flat=True)
    for oauth2_slug in oauth2_slugs:
        provider = OAuth2ProviderConfig.current(oauth2_slug)
        if provider.enabled_for_current_site: # and provider.backend_name in _PSA_OAUTH2_BACKENDS:
            providers.append(provider.backend_name)
    return providers
