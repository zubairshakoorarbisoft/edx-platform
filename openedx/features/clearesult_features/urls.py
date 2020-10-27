"""
URLs for clearesult app.
"""
from django.conf.urls import url, include

from openedx.features.clearesult_features.views import LoginView, ResetPasswordView, render_continuing_education

from openedx.features.clearesult_features.views import LoginView, ResetPasswordView
from openedx.features.clearesult_features.authentication.views import SiteSecurityView


app_name = 'clearesult_features'

urlpatterns = (
    url(
        r'^auth/login/$',
        LoginView.as_view(),
        name="auth"
    ),
    url(
        r'^auth/reset_password/$',
        ResetPasswordView.as_view(),
        name="reset_password"
    ),
    url(
        r'^continuing_education/$',
        render_continuing_education,
        name='continuing_education'
    ),
    url(
        r'^site_security/$',
        SiteSecurityView.as_view(),
        name="site_security_code"
    ),
    url(
        r'^api/v0/',
        include('openedx.features.clearesult_features.api.v0.urls', namespace='api_v0')
    )
)
