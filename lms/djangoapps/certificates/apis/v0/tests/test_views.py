"""
Tests for the Certificate REST APIs.
"""
from datetime import datetime, timedelta
import ddt
from enum import Enum
from mock import patch

from django.urls import reverse
from django.utils import timezone
from freezegun import freeze_time
from oauth2_provider import models as dot_models
from rest_framework import status
from rest_framework.test import APITestCase

from course_modes.models import CourseMode
from lms.djangoapps.certificates.apis.v0.views import CertificatesDetailView
from lms.djangoapps.certificates.models import CertificateStatuses
from lms.djangoapps.certificates.tests.factories import GeneratedCertificateFactory
from openedx.core.djangoapps.waffle_utils import WaffleSwitch
from openedx.core.lib.token_utils import JwtBuilder
from student.tests.factories import UserFactory
from xmodule.modulestore.tests.django_utils import SharedModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory

USER_PASSWORD = 'test'


TODO_REPLACE_SWITCH = WaffleSwitch('oauth', 'repace_with_scopes_flag')


class AuthType(Enum):
    session = 1
    oauth = 2
    jwt = 3


@ddt.ddt
class CertificatesRestApiTest(SharedModuleStoreTestCase, APITestCase):
    """
    Test for the Certificates REST APIs
    """
    shard = 4
    now = timezone.now()

    @classmethod
    def setUpClass(cls):
        super(CertificatesRestApiTest, cls).setUpClass()
        cls.course = CourseFactory.create(
            org='edx',
            number='verified',
            display_name='Verified Course'
        )

    def setUp(self):
        freezer = freeze_time(self.now)
        freezer.start()
        self.addCleanup(freezer.stop)

        super(CertificatesRestApiTest, self).setUp()

        self.student = UserFactory.create(password=USER_PASSWORD)
        self.student_no_cert = UserFactory.create(password=USER_PASSWORD)
        self.staff_user = UserFactory.create(password=USER_PASSWORD, is_staff=True)

        GeneratedCertificateFactory.create(
            user=self.student,
            course_id=self.course.id,
            status=CertificateStatuses.downloadable,
            mode='verified',
            download_url='www.google.com',
            grade="0.88"
        )

        self.namespaced_url = 'certificates_api:v0:certificates:detail'

    def _assert_certificate_response(self, response):
        self.assertEqual(
            response.data,
            {
                'username': self.student.username,
                'status': CertificateStatuses.downloadable,
                'is_passing': True,
                'grade': '0.88',
                'download_url': 'www.google.com',
                'certificate_type': CourseMode.VERIFIED,
                'course_id': unicode(self.course.id),
                'created_date': self.now,
            }
        )

    def _get_url(self, username):
        """
        Helper function to create the url for certificates
        """
        return reverse(
            self.namespaced_url,
            kwargs={
                'course_id': self.course.id,
                'username': username
            }
        )

    def _create_oauth_token(self, user):
        dot_app_user = UserFactory.create(password=USER_PASSWORD)
        dot_app = dot_models.Application.objects.create(
            name='test app',
            user=dot_app_user,
            client_type='confidential',
            authorization_grant_type='authorization-code',
            redirect_uris='http://localhost:8079/complete/edxorg/'
        )
        return dot_models.AccessToken.objects.create(
            user=user,
            application=dot_app,
            expires=datetime.utcnow() + timedelta(weeks=1),
            scope='read write',
            token='test_token',
        )

    def _create_jwt_token(self, user, scopes=None):
        return JwtBuilder(user).build_token(
            scopes
            if scopes is not None else CertificatesDetailView.required_scopes,
        )

    def _get_response(self, requesting_user, auth_type, url=None, token=None):
        auth_header = None
        if auth_type == AuthType.session:
            self.client.login(username=requesting_user.username, password=USER_PASSWORD)
        elif auth_type == AuthType.oauth:
            oauth_token = token if token else self._create_oauth_token(requesting_user)
            auth_header = "Bearer {0}".format(oauth_token)
        else:
            assert auth_type == AuthType.jwt
            jwt_token = token if token else self._create_jwt_token(requesting_user)
            auth_header = "JWT {0}".format(jwt_token)

        extra = dict(HTTP_AUTHORIZATION=auth_header) if auth_header else {}
        return self.client.get(
            url if url else self._get_url(self.student.username), 
            **extra
        )

    def test_anonymous_user(self):
        resp = self.client.get(self._get_url(self.student.username))
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    @ddt.data(*list(AuthType))
    def test_self_user(self, auth_type):
        resp = self._get_response(self.student, auth_type)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self._assert_certificate_response(resp)

    @ddt.data(*list(AuthType))
    def test_staff_user(self, auth_type):
        resp = self._get_response(self.staff_user, auth_type)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    @ddt.data(*list(AuthType))
    def test_inactive_user(self, auth_type):
        self.student.is_active = False
        self.student.save()

        resp = self._get_response(self.student, auth_type)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    @patch('edx_rest_framework_extensions.permissions.log')
    @ddt.data(*list(AuthType))
    def test_another_user(self, auth_type, mock_log):
        resp = self._get_response(self.student_no_cert, auth_type)
        self.assertEqual(
            resp.status_code,
            # JWT tokens without the user:me filter have access to other users
            status.HTTP_200_OK if auth_type == AuthType.jwt else status.HTTP_403_FORBIDDEN,
        )
        if auth_type != AuthType.jwt:
            self.assertTrue(mock_log.info.called)
            self.assertIn('IsUserInUrl', mock_log.info.call_args_list[0][0][0])

    @ddt.data(*list(AuthType))
    def test_no_certificate(self, auth_type):
        resp = self._get_response(
            self.student_no_cert,
            auth_type,
            url=self._get_url(self.student_no_cert.username),
        )
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('error_code', resp.data)
        self.assertEqual(
            resp.data['error_code'],
            'no_certificate_for_user',
        )

    @patch('edx_rest_framework_extensions.permissions.log')
    @ddt.data(True, False)
    def test_jwt_unrequired_scopes(self, scopes_enforced, mock_log):
        """ Returns 403 when scopes are enforced. """
        with TODO_REPLACE_SWITCH.override(active=scopes_enforced):
            jwt_token = self._create_jwt_token(
                self.student,
                scopes=[],
            )

            resp = self._get_response(self.student, AuthType.jwt, token=jwt_token)
            self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN if scopes_enforced else status.HTTP_200_OK)

            if scopes_enforced:
                self.assertTrue(mock_log.warning.called)
                self.assertIn("JwtHasScope", mock_log.call_args)

    @ddt.data(True, False)
    def test_jwt_on_behalf_of_user(self, scopes_enforced):
        with TODO_REPLACE_SWITCH.override(active=scopes_enforced):
            jwt_token = self._create_jwt_token(
                self.student,
                scopes=CertificatesDetailView.required_scopes + ['user:me'],
            )

            resp = self._get_response(self.student, AuthType.jwt, token=jwt_token)
            self.assertEqual(resp.status_code, status.HTTP_200_OK)

    @patch('edx_rest_framework_extensions.permissions.log')
    @ddt.data(True, False)
    def test_jwt_on_behalf_of_other_user(self, scopes_enforced, mock_log):
        """ Returns 403 when scopes are enforced. """
        with TODO_REPLACE_SWITCH.override(active=scopes_enforced):
            jwt_token = self._create_jwt_token(
                self.student_no_cert,
                scopes=CertificatesDetailView.required_scopes + ['user:me'],
            )

            resp = self._get_response(self.student, AuthType.jwt, token=jwt_token)
            self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN if scopes_enforced else status.HTTP_200_OK)

            if scopes_enforced:
                self.assertTrue(mock_log.warning.called)
                self.assertIn("JwtHasUserFilterForRequestedUser", mock_log.call_args)

    def test_valid_oauth_token(self):
        resp = self._get_response(self.student, AuthType.oauth)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_invalid_oauth_token(self):
        resp = self._get_response(self.student, AuthType.oauth, token="fooooooooooToken")
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_expired_oauth_token(self):
        token = self._create_oauth_token(self.student)
        token.expires = datetime.utcnow() - timedelta(weeks=1)
        token.save()
        resp = self._get_response(self.student, AuthType.oauth, token=token)
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)
