
from openedx.core.djangoapps.user_authn.cookies import delete_logged_in_cookies


class SessionCookieMiddleware(object):
    """
    Deletes the login session cookies if user is not authenticated
    """

    def process_response(self, request, response):
        if hasattr(request, 'user') and not request.user.is_authenticated:
            delete_logged_in_cookies(response)

        return response
