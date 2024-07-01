"""
URLs Edly app views.
"""

from django.conf.urls import url

from openedx.features.edly.views import account_deactivated_view
from openedx.features.edly.api.v1.views.chatly_view import ChatlyIntegrationView, ChatlyWebHook

urlpatterns = [
    url('account_deactivated/', account_deactivated_view, name='account_deactivated_view'),
    url(r'^api/integrate/chatly/', ChatlyIntegrationView.as_view(), name='chatly_integration_view'),
    url(r'^api/chatly/web_hook/', ChatlyWebHook.as_view(), name='chatly_web_hook'),
]
