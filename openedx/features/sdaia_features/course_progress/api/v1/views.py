"""
The User Watch Hours API view - SDAIA Specific.
"""

import logging
import requests

from django.conf import settings
from django.utils.decorators import method_decorator
from edx_rest_framework_extensions.auth.jwt.authentication import JwtAuthentication
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from common.djangoapps.util.disable_rate_limit import can_disable_rate_limit
from openedx.core.djangoapps.cors_csrf.decorators import ensure_csrf_cookie_cross_domain
from openedx.core.lib.api.authentication import BearerAuthenticationAllowInactiveUser
from openedx.core.lib.api.permissions import ApiKeyHeaderPermissionIsAuthenticated


log = logging.getLogger(__name__)


@can_disable_rate_limit
class UserWatchHoursAPIView(APIView, ApiKeyPermissionMixIn):
    authentication_classes = (
        JwtAuthentication,
        BearerAuthenticationAllowInactiveUser,
        EnrollmentCrossDomainSessionAuth,
    )
    permission_classes = (ApiKeyHeaderPermissionIsAuthenticated,)

    def sql_format(template, *args, **kwargs):
        args = [sql_escape_string(arg).decode() for arg in args]
        kwargs = {
            key: sql_escape_string(value).decode() for key, value in kwargs.items()
        }
        return template.format(*args, **kwargs)

    @method_decorator(ensure_csrf_cookie_cross_domain)
    def get(self, request):
        """
        Gets the total watch hours for a user.
        """
        user_id = request.user.id
        clickhouse_uri = (
            f"{settings.CAIRN_CLICKHOUSE_HTTP_SCHEME}://{settings.CAIRN_CLICKHOUSE_USERNAME}:{settings.CAIRN_CLICKHOUSE_PASSWORD}@"
            f"{settings.CAIRN_CLICKHOUSE_HOST}:{settings.CAIRN_CLICKHOUSE_HTTP_PORT}/?database={settings.CAIRN_CLICKHOUSE_DATABASE}"
        )
        query = self.sql_format(
            f"SELECT SUM(duration) as `Watch time` FROM `openedx`.`video_view_segments` WHERE user_id={user_id};"
        )
        try:
            response = requests.get(clickhouse_uri, data=query.encode("utf8"))
            watch_time = float(response.content.decode().strip()) / (60 * 60)
            return Response(status=status.HTTP_200_OK, data={"watch_time": watch_time})
        except Exception as e:
            log.error(
                f"Unable to fetch watch for user {user_id} due to this exception: {str(e)}"
            )
            raise HTTPException(status_code=500, detail=str(e))
