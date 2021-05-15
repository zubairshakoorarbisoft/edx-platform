from django.conf.urls import url

from .views import course_category, course_category_list


urlpatterns = [
    url(r'^$', course_category_list, name='course_category_list'),
    url(r'^(?P<slug>[\w-]+)$', course_category, name='course_category'),
]

