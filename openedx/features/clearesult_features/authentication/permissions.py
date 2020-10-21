"""
Permissions for authentication related views.
"""
from django.urls import reverse
from django.shortcuts import redirect

from openedx.features.clearesult_features.authentication.utils import is_user_authenticated_for_site


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
