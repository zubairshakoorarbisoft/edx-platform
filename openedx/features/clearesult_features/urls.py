"""
URLs for clearesult app.
"""
from django.conf.urls import include, url

from  openedx.features.clearesult_features.views import AuthenticationView

app_name = 'clearesult_features'
urlpatterns = (
    url(
        r'^auth/$',
        AuthenticationView.as_view(),
        name="auth"
    ),
)
