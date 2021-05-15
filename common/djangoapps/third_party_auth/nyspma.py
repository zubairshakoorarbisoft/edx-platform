"""
Usage:          A Python Social Auth backend that authenticates against
                NY State Podiatric Medical Association web site. Built for
                Open edX but can be used with any Identity Consumer client
                BaseOAuth2 provides most of the functionality needed to
                implement an oauth backend. This module primarily overrides
                some of the social_core module default values, plus, it
                implements a couple of methods that must be implements in the
                subclass:
                    get_user_details()
                    user_data()
NYSPMA contact information:
                admin team for https://associationdatabase.com
                David Zachrich dave@tcssoftware.com
                Tim Rorris tim@tcssoftware.com
Installation:   This modules assumes the existence of several python constants.
                1. For Open edX the following must be added to aws.py:
                NYSPMA_BACKEND_CLIENT_ID = AUTH_TOKENS.get('NYSPMA_BACKEND_CLIENT_ID', None)
                NYSPMA_BACKEND_CLIENT_SECRET = AUTH_TOKENS.get('NYSPMA_BACKEND_CLIENT_SECRET', None)
                * the production implementation adds default values based on whatever the client provided
                  leading up to deployment.
                2. each of these environment tokens must be added to lms.env.json
References:     https://python-social-auth-docs.readthedocs.io/en/latest/
                https://github.com/python-social-auth
                https://github.com/python-social-auth/social-core
                https://edx.readthedocs.io/projects/edx-installing-configuring-and-running/en/latest/configuration/tpa/
Test Users:
                USER			PASSWORD
                Testing1@test.com	Testing1
                Testing2@test.com	Testing2
                Testing3@test.com	Testing3
"""
import json
from urllib.parse import urlencode
from urllib.request import urlopen
from social_core.backends.oauth import BaseOAuth2
from django.conf import settings


from logging import getLogger
logger = getLogger(__name__)


class NYSPMAOAuth2(BaseOAuth2):
    """
    NYSPMA OAuth authentication backend.
    """
    name = 'nyspma'             # to set the name that appears in the django admin
                                # drop-down box, "Backend name" in the
                                # "Add Provider Configuration (OAuth)" screen

    DEBUG_LOG = False            # true if you want to create a log trace of
                                # calls to this module.


    """
    reference docs for these settings:
    https://python-social-auth-docs.readthedocs.io/en/latest/configuration/settings.html
    """
    ACCESS_TOKEN_METHOD = 'POST'
    REDIRECT_STATE = False

    """
    Provided directly by TCS Software.
    """
    BASE_URL = 'https://associationdatabase.com'
    AUTHORIZATION_URL = BASE_URL + '/oauth/authorize'
    ACCESS_TOKEN_URL = BASE_URL + '/oauth/token'
    USER_QUERY = BASE_URL + '/api/user?'
    AUTH_EXTRA_ARGUMENTS = {
    'org_id': 'NYSPMA'
    }
    SCOPE_SEPARATOR = ' '
    DEFAULT_SCOPE = ['public', 'write']

    ## these i'm not entirely sure about. i believe that downstream consumers
    ## of the authentication response -- in the 3rd party auth pipeline -- might
    ## receive a parameter re "extra data" but as of yet i have not see any
    ## examples of how this works.
    EXTRA_DATA = [
        ('id', 'id'),
        ('org_id', 'org_id'),
        ('date_joined', 'date_joined')
    ]

    """
    most of these defs are just scaffolding in the event of need for
    modifications in future.
    """

    def authorization_url(self):
        """
        ref on url parameters: https://markhneedham.com/blog/2019/01/11/python-add-query-parameters-url/
        """
        url = self.AUTHORIZATION_URL
        if self.DEBUG_LOG:
            logger.info('authorization_url(): {}'.format(url))
        return url

    def access_token_url(self):
        url = self.ACCESS_TOKEN_URL
        if self.DEBUG_LOG:
            logger.info('access_token_url(): {}'.format(url))
        return url

    def get_user_id(self, details, response):
        if self.DEBUG_LOG:
            logger.info('get_user_id() - response: {}'.format(details))
        return details['username']

    def get_username(self, strategy, details, backend, user=None, *args, **kwargs):
        if self.DEBUG_LOG:
            logger.info('get_username() - details: {}'.format(details))
        return details['username']

    def user_query(self):
        url = self.USER_QUERY
        if self.DEBUG_LOG:
            logger.info('user_query(): {}'.format(url))
        return url

    def urlopen(self, url):
        if self.DEBUG_LOG:
            logger.info('urlopen() - url: {}'.format(url))
        return urlopen(url).read().decode("utf-8")

    def auth_extra_arguments(self):
        """Return extra arguments needed on auth process. The defaults can be
        overridden by GET parameters."""
        extra_arguments = self.AUTH_EXTRA_ARGUMENTS
        if self.DEBUG_LOG:
            logger.info('auth_extra_arguments() - : {}'.format(extra_arguments))
        return extra_arguments

    """
    i believe that this is the json object that gets consumed within consumers
    of the 3rd party pipeline. we want these keys to match up with whatever
    Open edX is expecting.
    more details: https://github.com/edx/edx-platform/tree/master/common/djangoapps/third_party_auth
    """
    def get_user_details(self, response):
        """Return user details from NYSPMA account"""
        if self.DEBUG_LOG:
            logger.info('get_user_details() - response: {}'.format(response))

        access_token = response.get('access_token')
        user_details = self.user_data(access_token)
        username = str(user_details.get('id'))
        email = user_details.get('email_address', '')
        first_name = user_details.get('first_name')
        last_name = user_details.get('last_name')
        fullname = first_name + ' ' + last_name

        retval = dict([
            ('username', username),
            ('org_id', 'NYSPMA'),
            ('email', email),
            ('fullname', fullname),
            ('first_name', first_name),
            ('last_name', last_name)
        ])

        # self._set_association(email)

        if self.DEBUG_LOG:
            logger.info('get_user_details() - retval: {}'.format(retval))

        return retval

    """
    this will return a json object that exactly matches whatever the
    identify provider sends.
    """
    def user_data(self, access_token, *args, **kwargs):
        """Loads user data from service"""
        if self.DEBUG_LOG:
            logger.info('user_data() - entered')

        url = self.user_query() + urlencode({
            'access_token': access_token
        })
        return json.loads(self.urlopen(url))


    def get_key_and_secret(self):
        if self.DEBUG_LOG:
            logger.info('get_key_and_secret() - client_id: {}'.format(settings.NYSPMA_BACKEND_CLIENT_ID))

        return (settings.NYSPMA_BACKEND_CLIENT_ID, settings.NYSPMA_BACKEND_CLIENT_SECRET)

#    """
#        try to store the association name in a CME Online custom user field.
#    """
    # def _set_association(self, email):
    #     user = self._get_user(email)
    #     if user:
    #         association = Association.objects.get_or_create(user=user)[0]
    #         association.association_name = 'NYSPMA'
    #         association.save()

    #         if self.DEBUG_LOG:
    #             logger.info('_set_association() - saved association for : {}'.format(email))

    # def _get_user(self, email):
    #     try:
    #         user = get_user_by_username_or_email(email)
    #         return user
    #     except User.DoesNotExist:
    #         logger.warning('_set_association() - user does not exist {}'.format(email))
    #         return

