"""
Tests for logout
"""
import unittest

from django.conf import settings
from django.test import TestCase
from django.urls import reverse
from edx_oauth2_provider.constants import AUTHORIZED_CLIENTS_SESSION_KEY
from edx_oauth2_provider.tests.factories import (
    ClientFactory,
    TrustedClientFactory
)
from student.tests.factories import UserFactory


@unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
class LogoutTests(TestCase):
    """ Tests for the logout functionality. """

    def setUp(self):
        """ Create a course and user, then log in. """
        super(LogoutTests, self).setUp()
        self.user = UserFactory()
        self.client.login(username=self.user.username, password='test')

    def create_oauth_client(self):
        """ Creates a trusted OAuth client. """
        client = ClientFactory(logout_uri='https://www.example.com/logout/')
        TrustedClientFactory(client=client)
        return client

    def assert_session_logged_out(self, oauth_client, **logout_headers):
        """ Authenticates a user via OAuth 2.0, logs out, and verifies the session is logged out. """
        self.authenticate_with_oauth(oauth_client)

        # Logging out should remove the session variables, and send a list of logout URLs to the template.
        # The template will handle loading those URLs and redirecting the user. That functionality is not tested here.
        response = self.client.get(reverse('logout'), **logout_headers)
        self.assertEqual(response.status_code, 200)
        self.assertNotIn(AUTHORIZED_CLIENTS_SESSION_KEY, self.client.session)

        return response

    def authenticate_with_oauth(self, oauth_client):
        """ Perform an OAuth authentication using the current web client.

        This should add an AUTHORIZED_CLIENTS_SESSION_KEY entry to the current session.
        """
        data = {
            'client_id': oauth_client.client_id,
            'client_secret': oauth_client.client_secret,
            'response_type': 'code'
        }
        # Authenticate with OAuth to set the appropriate session values
        self.client.post(reverse('oauth2:capture'), data, follow=True)
        self.assertListEqual(self.client.session[AUTHORIZED_CLIENTS_SESSION_KEY], [oauth_client.client_id])

    def assert_logout_redirects_to_root(self):
        """ Verify logging out redirects the user to the homepage. """
        response = self.client.get(reverse('logout'))
        self.assertRedirects(response, '/', fetch_redirect_response=False)

    def assert_logout_redirects_with_target(self):
        """ Verify logging out with a redirect_url query param redirects the user to the target. """
        url = '{}?{}'.format(reverse('logout'), 'redirect_url=/courses')
        response = self.client.get(url)
        self.assertRedirects(response, '/courses', fetch_redirect_response=False)

    def test_without_session_value(self):
        """ Verify logout works even if the session does not contain an entry with
        the authenticated OpenID Connect clients."""
        self.assert_logout_redirects_to_root()
        self.assert_logout_redirects_with_target()

    def test_client_logout(self):
        """ Verify the context includes a list of the logout URIs of the authenticated OpenID Connect clients.

        The list should only include URIs of the clients for which the user has been authenticated.
        """
        client = self.create_oauth_client()
        response = self.assert_session_logged_out(client)
        expected = {
            'logout_uris': [client.logout_uri + '?no_redirect=1'],
            'target': '/',
        }
        self.assertDictContainsSubset(expected, response.context_data)

    def test_filter_referring_service(self):
        """ Verify that, if the user is directed to the logout page from a service, that service's logout URL
        is not included in the context sent to the template.
        """
        client = self.create_oauth_client()
        response = self.assert_session_logged_out(client, HTTP_REFERER=client.logout_uri)
        expected = {
            'logout_uris': [],
            'target': '/',
        }
        self.assertDictContainsSubset(expected, response.context_data)
