"""Learner dashboard views"""
from bulk_email.models import BulkEmailFlag, Optout  # pylint: disable=import-error

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.http import Http404
from django.shortcuts import redirect
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_GET

from edxmako.shortcuts import render_to_response, render_to_string
from commerce.utils import EcommerceService
from xmodule.modulestore.django import modulestore

from course_modes.models import CourseMode
from courseware.access import has_access
from lms.djangoapps.learner_dashboard.utils import FAKE_COURSE_KEY, strip_course_id
from openedx.core.djangoapps import monitoring_utils
from openedx.core.djangoapps.programs.models import ProgramsApiConfig
from openedx.core.djangoapps.programs.utils import (
    ProgramDataExtender,
    ProgramProgressMeter,
    get_certificates,
    get_program_marketing_url
)
from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers
from openedx.core.djangoapps.user_api.preferences.api import get_user_preferences
from openedx.features.enterprise_support.api import enterprise_customer_for_request
from shoppingcart.api import order_history
from student.cookies import set_user_info_cookie
from student.models import UserProfile
from student.views import (
    get_course_enrollments,
    get_org_black_and_whitelist_for_site,
    get_dashboard_consent_notification,
    complete_course_mode_info,
    consent_needed_for_course,
    _create_recent_enrollment_message,
    get_pre_requisite_courses_not_completed,
    _credit_statuses
)

@login_required
@require_GET
def program_listing(request):
    """View a list of programs in which the user is engaged."""
    programs_config = ProgramsApiConfig.current()
    if not programs_config.enabled:
        raise Http404

    meter = ProgramProgressMeter(request.site, request.user)

    context = {
        'disable_courseware_js': True,
        'marketing_url': get_program_marketing_url(programs_config),
        'nav_hidden': True,
        'programs': meter.engaged_programs,
        'progress': meter.progress(),
        'show_program_listing': programs_config.enabled,
        'show_dashboard_tabs': True,
        'uses_pattern_library': True,
    }

    return render_to_response('learner_dashboard/programs.html', context)


@login_required
@require_GET
def program_details(request, program_uuid):
    """View details about a specific program."""
    programs_config = ProgramsApiConfig.current()
    if not programs_config.enabled:
        raise Http404

    meter = ProgramProgressMeter(request.site, request.user, uuid=program_uuid)
    program_data = meter.programs[0]

    if not program_data:
        raise Http404

    program_data = ProgramDataExtender(program_data, request.user).extend()
    course_data = meter.progress(programs=[program_data], count_only=False)[0]
    certificate_data = get_certificates(request.user, program_data)

    program_data.pop('courses')
    skus = program_data.get('skus')
    ecommerce_service = EcommerceService()

    urls = {
        'program_listing_url': reverse('program_listing_view'),
        'track_selection_url': strip_course_id(
            reverse('course_modes_choose', kwargs={'course_id': FAKE_COURSE_KEY})
        ),
        'commerce_api_url': reverse('commerce_api:v0:baskets:create'),
        'buy_button_url': ecommerce_service.get_checkout_page_url(*skus)
    }

    context = {
        'urls': urls,
        'show_program_listing': programs_config.enabled,
        'show_dashboard_tabs': True,
        'nav_hidden': True,
        'disable_courseware_js': True,
        'uses_pattern_library': True,
        'user_preferences': get_user_preferences(request.user),
        'program_data': program_data,
        'course_data': course_data,
        'certificate_data': certificate_data
    }

    return render_to_response('learner_dashboard/program_details.html', context)


@login_required
@ensure_csrf_cookie
def dashboard(request):
    """
    Provides the LMS dashboard view

    TODO: This is lms specific and does not belong in common code.

    Arguments:
        request: The request object.

    Returns:
        The dashboard response.

    """
    user = request.user
    if not UserProfile.objects.filter(user=user).exists():
        return redirect(reverse('account_settings'))

    platform_name = configuration_helpers.get_value("platform_name", settings.PLATFORM_NAME)
    enable_verified_certificates = configuration_helpers.get_value(
        'ENABLE_VERIFIED_CERTIFICATES',
        settings.FEATURES.get('ENABLE_VERIFIED_CERTIFICATES')
    )
    display_course_modes_on_dashboard = configuration_helpers.get_value(
        'DISPLAY_COURSE_MODES_ON_DASHBOARD',
        settings.FEATURES.get('DISPLAY_COURSE_MODES_ON_DASHBOARD', True)
    )
    activation_email_support_link = configuration_helpers.get_value(
        'ACTIVATION_EMAIL_SUPPORT_LINK', settings.ACTIVATION_EMAIL_SUPPORT_LINK
    ) or settings.SUPPORT_SITE_LINK

    # get the org whitelist or the org blacklist for the current site
    site_org_whitelist, site_org_blacklist = get_org_black_and_whitelist_for_site(user)
    course_enrollments = list(get_course_enrollments(user, site_org_whitelist, site_org_blacklist))

    # Record how many courses there are so that we can get a better
    # understanding of usage patterns on prod.
    monitoring_utils.accumulate('num_courses', len(course_enrollments))

    # sort the enrollment pairs by the enrollment date
    course_enrollments.sort(key=lambda x: x.created, reverse=True)

    # Retrieve the course modes for each course
    enrolled_course_ids = [enrollment.course_id for enrollment in course_enrollments]
    __, unexpired_course_modes = CourseMode.all_and_unexpired_modes_for_courses(enrolled_course_ids)
    course_modes_by_course = {
        course_id: {
            mode.slug: mode
            for mode in modes
        }
        for course_id, modes in unexpired_course_modes.iteritems()
    }

    # Check to see if the student has recently enrolled in a course.
    # If so, display a notification message confirming the enrollment.
    enrollment_message = _create_recent_enrollment_message(
        course_enrollments, course_modes_by_course
    )

    course_optouts = Optout.objects.filter(user=user).values_list('course_id', flat=True)

    sidebar_account_activation_message = ''
    banner_account_activation_message = ''
    display_account_activation_message_on_sidebar = configuration_helpers.get_value(
        'DISPLAY_ACCOUNT_ACTIVATION_MESSAGE_ON_SIDEBAR',
        settings.FEATURES.get('DISPLAY_ACCOUNT_ACTIVATION_MESSAGE_ON_SIDEBAR', False)
    )

    # Display activation message in sidebar if DISPLAY_ACCOUNT_ACTIVATION_MESSAGE_ON_SIDEBAR
    # flag is active. Otherwise display existing message at the top.
    if display_account_activation_message_on_sidebar and not user.is_active:
        sidebar_account_activation_message = render_to_string(
            'registration/account_activation_sidebar_notice.html',
            {
                'email': user.email,
                'platform_name': platform_name,
                'activation_email_support_link': activation_email_support_link
            }
        )
    elif not user.is_active:
        banner_account_activation_message = render_to_string(
            'registration/activate_account_notice.html',
            {'email': user.email}
        )

    enterprise_message = get_dashboard_consent_notification(request, user, course_enrollments)

    enterprise_customer = enterprise_customer_for_request(request)
    consent_required_courses = set()
    enterprise_customer_name = None
    if enterprise_customer:
        consent_required_courses = {
            enrollment.course_id for enrollment in course_enrollments
            if consent_needed_for_course(request, request.user, str(enrollment.course_id), True)
        }
        enterprise_customer_name = enterprise_customer['name']

    # Account activation message
    account_activation_messages = [
        message for message in messages.get_messages(request) if 'account-activation' in message.tags
    ]

    # Global staff can see what courses encountered an error on their dashboard
    staff_access = False
    errored_courses = {}
    if has_access(user, 'staff', 'global'):
        # Show any courses that encountered an error on load
        staff_access = True
        errored_courses = modulestore().get_errored_courses()

    show_courseware_links_for = frozenset(
        enrollment.course_id for enrollment in course_enrollments
        if has_access(request.user, 'load', enrollment.course_overview)
    )

    # Find programs associated with course runs being displayed. This information
    # is passed in the template context to allow rendering of program-related
    # information on the dashboard.
    meter = ProgramProgressMeter(request.site, user, enrollments=course_enrollments)
    inverted_programs = meter.invert_programs()

    # Construct a dictionary of course mode information
    # used to render the course list.  We re-use the course modes dict
    # we loaded earlier to avoid hitting the database.
    course_mode_info = {
        enrollment.course_id: complete_course_mode_info(
            enrollment.course_id, enrollment,
            modes=course_modes_by_course[enrollment.course_id]
        )
        for enrollment in course_enrollments
    }

    # Determine the per-course verification status
    # This is a dictionary in which the keys are course locators
    # and the values are one of:
    #
    # VERIFY_STATUS_NEED_TO_VERIFY
    # VERIFY_STATUS_SUBMITTED
    # VERIFY_STATUS_APPROVED
    # VERIFY_STATUS_MISSED_DEADLINE
    #
    # Each of which correspond to a particular message to display
    # next to the course on the dashboard.
    #
    # If a course is not included in this dictionary,
    # there is no verification messaging to display.
    verify_status_by_course = check_verify_status_by_course(user, course_enrollments)
    cert_statuses = {
        enrollment.course_id: cert_info(request.user, enrollment.course_overview, enrollment.mode)
        for enrollment in course_enrollments
    }

    # only show email settings for Mongo course and when bulk email is turned on
    show_email_settings_for = frozenset(
        enrollment.course_id for enrollment in course_enrollments if (
            BulkEmailFlag.feature_enabled(enrollment.course_id)
        )
    )

    # Verification Attempts
    # Used to generate the "you must reverify for course x" banner
    verification_status, verification_error_codes = SoftwareSecurePhotoVerification.user_status(user)
    verification_errors = get_verification_error_reasons_for_display(verification_error_codes)

    # Gets data for midcourse reverifications, if any are necessary or have failed
    statuses = ["approved", "denied", "pending", "must_reverify"]
    reverifications = reverification_info(statuses)

    block_courses = frozenset(
        enrollment.course_id for enrollment in course_enrollments
        if is_course_blocked(
            request,
            CourseRegistrationCode.objects.filter(
                course_id=enrollment.course_id,
                registrationcoderedemption__redeemed_by=request.user
            ),
            enrollment.course_id
        )
    )

    enrolled_courses_either_paid = frozenset(
        enrollment.course_id for enrollment in course_enrollments
        if enrollment.is_paid_course()
    )

    # If there are *any* denied reverifications that have not been toggled off,
    # we'll display the banner
    denied_banner = any(item.display for item in reverifications["denied"])

    # Populate the Order History for the side-bar.
    order_history_list = order_history(user, course_org_filter=site_org_whitelist, org_filter_out_set=site_org_blacklist)

    # get list of courses having pre-requisites yet to be completed
    courses_having_prerequisites = frozenset(
        enrollment.course_id for enrollment in course_enrollments
        if enrollment.course_overview.pre_requisite_courses
    )
    courses_requirements_not_met = get_pre_requisite_courses_not_completed(user, courses_having_prerequisites)

    if 'notlive' in request.GET:
        redirect_message = _("The course you are looking for does not start until {date}.").format(
            date=request.GET['notlive']
        )
    elif 'course_closed' in request.GET:
        redirect_message = _("The course you are looking for is closed for enrollment as of {date}.").format(
            date=request.GET['course_closed']
        )
    else:
        redirect_message = ''

    valid_verification_statuses = ['approved', 'must_reverify', 'pending', 'expired']
    display_sidebar_on_dashboard = len(order_history_list) or verification_status in valid_verification_statuses

    context = {
        'enterprise_message': enterprise_message,
        'consent_required_courses': consent_required_courses,
        'enterprise_customer_name': enterprise_customer_name,
        'enrollment_message': enrollment_message,
        'redirect_message': redirect_message,
        'account_activation_messages': account_activation_messages,
        'course_enrollments': course_enrollments,
        'course_optouts': course_optouts,
        'banner_account_activation_message': banner_account_activation_message,
        'sidebar_account_activation_message': sidebar_account_activation_message,
        'staff_access': staff_access,
        'errored_courses': errored_courses,
        'show_courseware_links_for': show_courseware_links_for,
        'all_course_modes': course_mode_info,
        'cert_statuses': cert_statuses,
        'credit_statuses': _credit_statuses(user, course_enrollments),
        'show_email_settings_for': show_email_settings_for,
        'reverifications': reverifications,
        'verification_status': verification_status,
        'verification_status_by_course': verify_status_by_course,
        'verification_errors': verification_errors,
        'block_courses': block_courses,
        'denied_banner': denied_banner,
        'billing_email': settings.PAYMENT_SUPPORT_EMAIL,
        'user': user,
        'logout_url': reverse('logout'),
        'platform_name': platform_name,
        'enrolled_courses_either_paid': enrolled_courses_either_paid,
        'provider_states': [],
        'order_history_list': order_history_list,
        'courses_requirements_not_met': courses_requirements_not_met,
        'nav_hidden': True,
        'inverted_programs': inverted_programs,
        'show_program_listing': ProgramsApiConfig.is_enabled(),
        'show_dashboard_tabs': True,
        'disable_courseware_js': True,
        'display_course_modes_on_dashboard': enable_verified_certificates and display_course_modes_on_dashboard,
        'display_sidebar_on_dashboard': display_sidebar_on_dashboard,
    }

    ecommerce_service = EcommerceService()
    if ecommerce_service.is_enabled(request.user):
        context.update({
            'use_ecommerce_payment_flow': True,
            'ecommerce_payment_page': ecommerce_service.payment_page_url(),
        })

    response = render_to_response('dashboard.html', context)
    set_user_info_cookie(response, request)
    return response
