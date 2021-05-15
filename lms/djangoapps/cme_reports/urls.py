from django.conf.urls import url
from django.conf import settings
from .views import course_list_report, course_orders_report, course_certificates_report, export_course_certificates_report

urlpatterns = [
    url(r'^courses$', course_list_report, name='reports_course_list'),
    url(r'^courses/{}/orders$'.format(settings.COURSE_ID_PATTERN), course_orders_report, name='reports_course_orders'),
    url(r'^courses/{}/certificates$'.format(settings.COURSE_ID_PATTERN), course_certificates_report, name='reports_course_certificates'),
    url(r'^courses/{}/certificates/export/$'.format(settings.COURSE_ID_PATTERN), export_course_certificates_report, name='export_course_certificates'),
]

