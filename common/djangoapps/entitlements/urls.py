from django.conf.urls import url, patterns
from django.conf import settings
from .views import EntitlementView, AddEntitlementView

urlpatterns = patterns(
    'entitlements.views',
    url(
        r'^list/{username}$'.format(username=settings.USERNAME_PATTERN),
        EntitlementView.as_view(), name='course_entitlement'
    ),
    url(r'^add', AddEntitlementView.as_view(), name='course_entitlement'),

)
