from django.conf.urls import include, url

app_name = 'edly_panel'

urlpatterns = [
    url(r'^v1/', include('openedx.features.edly_panel.api.v1.urls')),
]
