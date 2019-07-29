
from django.conf.urls import url

from .views import get_user_status

urlpatterns = [
    url(r'user-status', get_user_status, name='get_user_status'),
]
