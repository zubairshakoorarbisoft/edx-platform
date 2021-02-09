import logging

from django.conf import settings
from django.contrib.auth import logout
from django.core.cache import cache
from django.http import HttpResponseRedirect, Http404
from django.utils.deprecation import MiddlewareMixin
from six.moves.urllib.parse import urlencode

from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers
from openedx.features.clearesult_features.auth_backend import ClearesultAzureADOAuth2
from openedx.features.clearesult_features.models import ClearesultUserProfile
import third_party_auth
from third_party_auth import pipeline

LOGGER = logging.getLogger(__name__)


class ClearesultAuthenticationMiddleware(MiddlewareMixin):
    """
    Verify User's accessibility over his requested site
    """
    def process_request(self, request):
        """
        Django middleware hook for processing request
        """
        # TODO: Need to fix this suspicious user functionality
        # When we try to Click on enroll now button specifically
        # for paid courses we are getting a request with AnonymousUser
        # which is causing problems
        # if self._is_user_suspicious(request):
        #     return logout(request)

        allowed_sub_paths = getattr(settings, 'CLEARESULT_ALLOWED_SUB_PATHS', [])
        allowed_full_paths = getattr(settings, 'CLEARESULT_ALLOWED_FULL_PATHS', [])

        is_allowed = any([request.path.startswith(path) for path in allowed_sub_paths])
        is_allowed = is_allowed or any([request.path == path for path in allowed_full_paths])
        user = request.user

        reset_password_error = request.GET.get('error_description', '')
        if (reset_password_error and
                reset_password_error.startswith(getattr(settings, 'AZUREAD_B2C_FORGET_PASSWORD_CODE', 'N/A'))):

            reset_password_link = configuration_helpers.get_value('RESET_PASSWORD_LINK')
            if reset_password_link:
                LOGGER.info('Redirectiog to Azure AD B2C reset password link.')
                return HttpResponseRedirect(reset_password_link)

        if not settings.FEATURES.get('ENABLE_AZURE_AD_LOGIN_REDIRECTION', False) or is_allowed or user.is_authenticated:
            LOGGER.info('Leaving without redirection for {}'.format(request.path))
            return

        return self._redirect_to_login(request)

    def _redirect_to_login(self, request):
        backend_name = ClearesultAzureADOAuth2.name

        if third_party_auth.is_enabled() and backend_name:
            provider = [enabled for enabled in third_party_auth.provider.Registry.enabled()
                        if enabled.backend_name == backend_name]
            fallback_url = '{}/login'.format(configuration_helpers.get_value('LMS_BASE'))
            if not provider and fallback_url:
                next_url = urlencode({'next': self._get_current_url(request).replace('login', 'home')})
                redirect_url = '//{}?{}'.format(fallback_url, next_url)
                LOGGER.info('No Auth Provider found, redirecting to "{}"'.format(redirect_url))
                redirect_url = redirect_url.replace('signin_redirect_to_lms', 'home')
                return HttpResponseRedirect(redirect_url)
            elif provider:
                login_url = pipeline.get_login_url(
                    provider[0].provider_id,
                    pipeline.AUTH_ENTRY_LOGIN,
                    redirect_url=request.GET.get('next') if request.GET.get('next') else request.path,
                )
                LOGGER.info('Redirecting User to Auth Provider: {}'.format(backend_name))
                return HttpResponseRedirect(login_url)

        LOGGER.error('Unable to redirect, Auth Provider is not configured properly')
        raise Http404

    def _get_request_schema(self, request):
        """
        Returns schema of request
        """
        environ = getattr(request, 'environ', {})
        return environ.get('wsgi.url_scheme', 'http')

    def _get_current_url(self, request):
        """
        Returns current request's complete url
        """
        schema = self._get_request_schema(request)
        domain = self._get_request_site_domain(request)

        return '{}://{}{}'.format(schema, domain, request.path)

    def _get_request_site_domain(self, request):
        """
        Returns domain of site being requested by the User.
        """
        site = getattr(request, 'site', None)
        domain = getattr(site, 'domain', None)
        return domain

    def _is_user_suspicious(self, request):
        user = request.user
        if user.is_authenticated:
            if user.is_superuser:
                return False
            elif request.site.name in cache.get('clearesult_allowed_site_names', []):
                return False

            site_name = '-'.join(request.site.name.split('-')[:-1]).rstrip()
            try:
                clearesult_allowed_site_names = user.clearesult_profile.get_extension_value('site_identifier', [])
            except ClearesultUserProfile.DoesNotExist:
                return False

            cache.set('clearesult_allowed_site_names', clearesult_allowed_site_names, 864000)

            if site_name in clearesult_allowed_site_names:
                return False
            else:
                return True
