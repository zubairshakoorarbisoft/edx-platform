"""
Public views
"""

from urllib.parse import quote_plus

from django.conf import settings
from django.http.response import Http404
from django.shortcuts import redirect

from common.djangoapps.edxmako.shortcuts import render_to_response
from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers

from ..config.waffle import ENABLE_ACCESSIBILITY_POLICY_PAGE

__all__ = [
    'register_redirect_to_lms', 'login_redirect_to_lms', 'howitworks', 'accessibility',
    'redirect_to_lms_login_for_admin',
]


def register_redirect_to_lms(request):
    """
    This view redirects to the LMS register view. It is used to temporarily keep the old
    Studio signup url alive.
    """
    frontend_register_url = configuration_helpers.get_value(
        "FRONTEND_REGISTER_URL", settings.FRONTEND_REGISTER_URL
    )
    register_url = '{register_url}{params}'.format(
        register_url=frontend_register_url,
        params=_build_next_param(request),
    )
    return redirect(register_url, permanent=True)


def login_redirect_to_lms(request):
    """
    This view redirects to the LMS login view. It is used for Django's LOGIN_URL
    setting, which is where unauthenticated requests to protected endpoints are redirected.
    """
    frontend_login_url = configuration_helpers.get_value(
        "FRONTEND_LOGIN_URL", settings.FRONTEND_LOGIN_URL
    )
    login_url = '{login_url}{params}'.format(
        login_url=frontend_login_url,
        params=_build_next_param(request),
    )
    return redirect(login_url)


def redirect_to_lms_login_for_admin(request):
    """
    This view redirect the admin/login url to the site's login page.
    """
    return redirect('/login?next=/admin')


def _build_next_param(request):
    """ Returns the next param to be used with login or register. """
    next_url = request.GET.get('next')
    next_url = next_url if next_url else settings.LOGIN_REDIRECT_URL
    if next_url:
        # Warning: do not use `build_absolute_uri` when `next_url` is empty because `build_absolute_uri` would
        # build use the login url for the next url, which would cause a login redirect loop.
        absolute_next_url = request.build_absolute_uri(next_url)
        return '?next=' + quote_plus(absolute_next_url)
    return ''


def howitworks(request):
    "Proxy view"
    if request.user.is_authenticated:
        return redirect('/home/')
    else:
        return render_to_response('howitworks.html', {})


def accessibility(request):
    """
    Display the accessibility accommodation form.
    """
    if ENABLE_ACCESSIBILITY_POLICY_PAGE.is_enabled():
        return render_to_response('accessibility.html', {
            'language_code': request.LANGUAGE_CODE
        })
    raise Http404
