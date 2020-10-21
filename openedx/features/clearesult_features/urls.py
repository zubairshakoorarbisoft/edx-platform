"""
URLs for clearesult app.
"""
from django.conf.urls import url, include

from openedx.features.clearesult_features.views import LoginView, ResetPasswordView, render_continuing_education


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
        r'^api/v0/',
        include('openedx.features.clearesult_features.api.v0.urls', namespace='api_v0')
    )
)
