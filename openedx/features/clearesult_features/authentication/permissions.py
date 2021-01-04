"""
Permissions for authentication related views.
"""
from django.urls import reverse
from django.shortcuts import redirect
from django.http import HttpResponseForbidden

from openedx.features.clearesult_features.authentication.utils import is_user_authenticated_for_site
from openedx.features.clearesult_features.api.v0.validators import validate_sites_for_local_admin


def non_site_authenticated_user_required(view_fn):
    """
    Ensures that only a user that is not authenticated for current site
    can access the view.
    """

    def inner(_self, request, *args, **kwargs):
        if is_user_authenticated_for_site(request):
            return redirect(reverse('dashboard'))
        return view_fn(_self, request, *args, **kwargs)

    return inner


def local_admin_required(view_fn):
    """
    Ensures that only a user that is not authenticated for current site
    can access the view.
    """

    def inner(request, *args, **kwargs):
        error_response, allowed_sites = validate_sites_for_local_admin(request.user)

        # neither a super user nor local admin
        if error_response:
            return HttpResponseForbidden()

        return view_fn(request, *args, **kwargs)

    return inner
