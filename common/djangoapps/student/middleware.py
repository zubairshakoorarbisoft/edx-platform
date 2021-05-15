"""
Middleware that checks user standing for the purpose of keeping users with
disabled accounts from accessing the site.
"""


from django.conf import settings
from django.http import HttpResponseForbidden
from django.utils.deprecation import MiddlewareMixin
from django.utils.translation import ugettext as _
from django.shortcuts import redirect
from django.urls import reverse

from openedx.core.djangolib.markup import HTML, Text
from common.djangoapps.student.models import UserStanding


class UserStandingMiddleware(MiddlewareMixin):
    """
    Checks a user's standing on request. Returns a 403 if the user's
    status is 'disabled'.
    """
    def process_request(self, request):
        user = request.user
        try:
            user_account = UserStanding.objects.get(user=user.id)
            # because user is a unique field in UserStanding, there will either be
            # one or zero user_accounts associated with a UserStanding
        except UserStanding.DoesNotExist:
            pass
        else:
            if user_account.account_status == UserStanding.ACCOUNT_DISABLED:
                msg = Text(_(
                    'Your account has been disabled. If you believe '
                    'this was done in error, please contact us at '
                    '{support_email}'
                )).format(
                    support_email=HTML(u'<a href="mailto:{address}?subject={subject_line}">{address}</a>').format(
                        address=settings.DEFAULT_FEEDBACK_EMAIL,
                        subject_line=_('Disabled Account'),
                    ),
                )
                return HttpResponseForbidden(msg)


class CheckNPIMiddleware(MiddlewareMixin):
    """
    Check if user has set NPI or not
    """
    def process_request(self, request):
        account_settings_url = reverse('account_settings')
        user = request.user
        is_logout = (reverse('logout') == request.path)
        is_authenticated = user.is_authenticated
        # import pdb;pdb.set_trace()
        is_url_match = request.path in [reverse('root'), reverse('dashboard'), reverse('courses'), reverse('course_category_list')]
        is_url_match = request.path.startswith(reverse('courses')) or request.path.startswith(reverse('course_category_list')) or is_url_match
        if is_url_match and is_authenticated and hasattr(user, 'profile'):
            if not user.profile.npi and not (user.is_superuser or is_logout or account_settings_url == request.path):
                return redirect(account_settings_url + '?highlight=npi')
            if not (user.profile.state and user.profile.city) and not (user.is_superuser or is_logout or account_settings_url == request.path):
                return redirect(account_settings_url + '?highlight=state-city')

