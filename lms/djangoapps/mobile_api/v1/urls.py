"""
URLs for mobile API
"""

from django.conf.urls import include, url

urlpatterns = [
    url(r'^users/', include('mobile_api.v1.users.urls')),
]
