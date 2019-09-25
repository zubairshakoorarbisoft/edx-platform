from django.conf.urls import url
from rest_framework.routers import DefaultRouter

from openedx.features.edly_panel.api.v1 import views

app_name = 'v1'
urlpatterns = [
    url(r'', views.get_maus),
]
