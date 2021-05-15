import csv
import json

from django.http import Http404, HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q

from edxmako.shortcuts import render_to_response
from opaque_keys.edx.keys import CourseKey
from course_modes.models import CourseMode
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from openedx.core.djangoapps.commerce.utils import ecommerce_api_client
from lms.djangoapps.certificates.models import GeneratedCertificate
from common.djangoapps.course_category.models import CourseCategory
from .serializers import CourseListSerializer, CourseCertificateSerializers

NUM_OF_RECORDS_PER_PAGE = 100

@login_required
def course_list_report(request):
    """
    return list of courses with id, name, category, enrollment count, and mode
    Accessible for staff or superusers only
    """
    if not (request.user.is_superuser):
        raise Http404
    course_modes_qs = CourseMode.objects.all()
    page = request.GET.get('page', 1)
    search = request.GET.get('search', '')
    if search:
        course_modes_qs = course_modes_qs.filter(Q(course__display_name__icontains=search) | Q(course__id__icontains=search))
    paginator = Paginator(course_modes_qs, NUM_OF_RECORDS_PER_PAGE)

    try:
        modes_page = paginator.page(page)
    except PageNotAnInteger:
        modes_page = paginator.page(1)
    except EmptyPage:
        modes_page = paginator.page(paginator.num_pages)

    course_modes = CourseListSerializer(modes_page.object_list, many=True)
    context = {
        'courses': course_modes.data,
        'course_modes_page': modes_page,
        'search_string': search,
    }

    return render_to_response('cme_reports/course_list.html', context)


@login_required
def course_orders_report(request, course_id):
    """
    call ecommerce api to get course orders details. returns course order details.
    """
    if not (request.user.is_superuser):
        raise Http404

    ecommerce_api = ecommerce_api_client(request.user)
    orders = ecommerce_api.cme_report.get_course_orders.post(
        json.dumps({
            'course_id': course_id,
        })
    )
    #orders = orders.get('report_json', [])
    orders = orders.get('course_orders', [])

    course_key = CourseKey.from_string(course_id)
    course_name = CourseOverview.get_from_id(course_key).display_name
    categories_list = CourseCategory.get_course_category(course_key).values_list('name', flat=True)

    context = {
        'course_name': course_name,
        'category': ', '.join(categories_list),
        'instructors': 'test1@example.com, test2@example.com',
        'orders': orders
    }
    return render_to_response('cme_reports/course_orders_list.html', context)


@login_required
def course_certificates_report(request, course_id):
    """
    Returns all certificate details of requested course id
    """
    if not (request.user.is_superuser):
        raise Http404
    course_mode = request.GET.get('course_mode', "")
    page = request.GET.get('page', 1)
    search = request.GET.get('search', '')

    course_key = CourseKey.from_string(course_id)
    course_name = CourseOverview.get_from_id(course_key).display_name
    categories_list = CourseCategory.get_course_category(course_key).values_list('name', flat=True)
    cert_queryset = GeneratedCertificate.objects.filter(course_id=course_key, mode=course_mode)
    if search:
        cert_queryset = cert_queryset.filter(Q(user__profile__name__icontains=search) | Q(user__email__icontains=search))
    paginator = Paginator(cert_queryset, NUM_OF_RECORDS_PER_PAGE)

    try:
        modes_page = paginator.page(page)
    except PageNotAnInteger:
        modes_page = paginator.page(1)
    except EmptyPage:
        modes_page = paginator.page(paginator.num_pages)

    course_certificates = CourseCertificateSerializers(modes_page.object_list, many=True)

    context = {
        'course_name': course_name,
        'category': ', '.join(categories_list),
        'instructors': 'test1@example.com, test2@example.com',
        'certificate_data': course_certificates.data,
        'course_mode': course_mode,
        'cert_page': modes_page,
        'search_string': search,
        'course_id': course_id,
    }
    return render_to_response('cme_reports/course_certificates_list.html', context)


def export_course_certificates_report(request, course_id):
    """
        export all certificate details in csv file of requested course id
    """
    if not (request.user.is_superuser):
        raise Http404

    course_mode = request.GET.get('course_mode', "")
    course_key = CourseKey.from_string(course_id)

    cert_queryset = GeneratedCertificate.objects.filter(course_id=course_key, mode=course_mode)
    course_certificates = CourseCertificateSerializers(cert_queryset, many=True)

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="course_certificates.csv"'

    writer = csv.writer(response)
    writer.writerow(['ID', 'Completed On', 'Name', 'Email', 'NPI', 'State', 'City', 'Course ID', 'Mode'])
    for cert_detail in course_certificates.data:
        writer.writerow([
            cert_detail['verify_uuid'],
            cert_detail['created_date'],
            cert_detail['user_fullname'].encode("utf-8").decode("utf-8"),
            cert_detail['user_email'].encode("utf-8").decode("utf-8"),
            cert_detail['user_npi'].encode("utf-8").decode("utf-8"),
            cert_detail['user_state'].encode("utf-8").decode("utf-8"),
            cert_detail['user_city'].encode("utf-8").decode("utf-8"),
            course_id.encode("utf-8").decode("utf-8"),
            course_mode
        ])

    return response
