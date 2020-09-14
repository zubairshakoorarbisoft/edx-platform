"""
URLs for clearesult app.
"""
from django.conf.urls import include, url

from  openedx.features.clearesult_features.views import LoginView, ResetPasswordView

app_name = 'clearesult_features'
urlpatterns = (
    url(
        r'^auth/login$',
        LoginView.as_view(),
        name="auth"
    ),
    url(
        r'^auth/reset_password$',
        ResetPasswordView.as_view(),
        name="reset_password"
    ),
)
