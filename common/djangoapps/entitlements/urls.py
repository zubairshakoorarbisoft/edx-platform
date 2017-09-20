from django.conf.urls import url, patterns
from django.conf import settings
from .views import EntitlementView

urlpatterns = patterns(
    'entitlements.views',
    url(r'^entitlement/$', EntitlementView.as_view(), name='test')
)
