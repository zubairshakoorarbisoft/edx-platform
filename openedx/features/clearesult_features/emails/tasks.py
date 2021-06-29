import logging
import six
from celery import task
from celery_utils.logged_task import LoggedTask
from datetime import datetime

from django.contrib.sites.models import Site
from django.contrib.auth.models import User
from django.conf import settings
from django.test import RequestFactory
from student.models import CourseEnrollment

from openedx.features.clearesult_features.emails.task_utils import (
    get_site_courses, get_about_to_expire_trainings,
    get_eligible_enrolled_users_for_reminder_emails
)
from openedx.features.clearesult_features.models import ClearesultGroupLinkedCatalogs, ClearesultGroupLinkage
from openedx.features.clearesult_features.utils import (
    get_site_users,
    send_course_end_reminder_email,
    send_event_start_reminder_email
)

logger = logging.getLogger('edx.celery.task')


def _log_reminder_emails_report(expire_trainings, error_trainings, courses_emails_count, events_emails_count, events_error_emails, courses_error_emails):
    logger.info('\n\n\n')
    logger.info("--------------------- REMINDER EMAILS STATS - {} ---------------------".format(
        datetime.now().date().strftime("%m-%d-%Y")
    ))

    logger.info('Total number of about to expire trainings: {}'.format(len(expire_trainings)))
    logger.info('Trainings encountered processing error: {}'.format(len(error_trainings)))

    logger.info('Total number users who should get reminder email of courses: {}'.format(courses_emails_count))
    logger.info('Total number users who should get reminder email of events: {}'.format(events_emails_count))

    logger.info('Error encountered for event reminder emails: {}'.format(len(events_error_emails)))
    logger.info('Error encountered for courses reminder emails: {}'.format(len(courses_error_emails)))

    logger.info('Unable to send reminder emails of events: {}'.format(events_error_emails))
    logger.info('Unable to send reminder emails of courses: {}'.format(courses_error_emails))


@task(base=LoggedTask)
def check_and_send_reminder_emails():
    request = RequestFactory().get(u'/')
    sites = Site.objects.filter(name__icontains="LMS")

    # super user that will be used to send emails
    request.user = User.objects.get(username=settings.ADMIN_USERNAME_FOR_EMAIL_TASK)

    #some variables for starts
    email_count_for_courses = email_count_for_events = 0
    emails_error_for_courses = []
    emails_error_for_events = []
    processing_error_on_trainings = []
    about_to_expire_trainings = []

    for site in sites:
        request.site = site
        site_config = site.clearesult_configuration.latest('change_date')
        site_groups = ClearesultGroupLinkage.objects.filter(site=site).prefetch_related(
            'clearesultgrouplinkedcatalogs_set__catalog',
            'clearesultgrouplinkedcatalogs_set__mandatory_courses'
        )
        site_courses = get_site_courses(site_groups)
        site_users = get_site_users(site)
        about_to_expire_trainings.extend(get_about_to_expire_trainings(site_config, site_courses))
        for training in about_to_expire_trainings:
            try:
                enrollments = CourseEnrollment.objects.filter(
                    is_active=True,
                    course_id=training.course_id,
                    user__in=site_users
                )
                if training.is_event:
                    # for event - send reminder email to all registered users
                    users = [enrollment.user for enrollment in enrollments]
                    email_count_for_events += len(users)
                    send_event_start_reminder_email(users, training, request, site_config.events_notification_period, emails_error_for_events)

                else:
                    # enrollments are only eligible for the emails if course is not mandatory for that user
                    # and enrolled user has not completed course.
                    users = get_eligible_enrolled_users_for_reminder_emails(request, training, enrollments, site_groups)
                    email_count_for_courses += len(users)
                    send_course_end_reminder_email(
                        users, training, request, site_config.courses_notification_period, emails_error_for_courses)
            except Exception as ex:
                logger.error(ex)
                processing_error_on_trainings.append(six.text_type(training.course_id))

    _log_reminder_emails_report(
        about_to_expire_trainings, processing_error_on_trainings, email_count_for_courses,
        email_count_for_events, emails_error_for_events, emails_error_for_courses
    )
