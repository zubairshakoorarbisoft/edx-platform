"""
Django management command to generate a send email to user at different progresses for a course
"""


import json
import logging

from celery import shared_task
from django.contrib.auth.models import User  # lint-amnesty, pylint: disable=imported-auth-user
from django.contrib.sites.models import Site
from django.core.management.base import BaseCommand

from common.djangoapps.student.models import CourseEnrollment
from lms.djangoapps.courseware.models import StudentModule
from lms.djangoapps.courseware.courses import get_course_blocks_completion_summary
from lms.djangoapps.grades.api import CourseGradeFactory
from xmodule.course_block import CourseFields  # lint-amnesty, pylint: disable=wrong-import-order
from xmodule.modulestore.django import modulestore

logger = logging.getLogger(__name__)

########### Models.py
from django.contrib.auth.models import User  # lint-amnesty, pylint: disable=imported-auth-user
from django.db import models

from opaque_keys.edx.django.models import CourseKeyField
class CourseCompletionEmailHistory(models.Model):
    """
    Keeps progress for a student for which he/she gets an email as he/she reaches at that particluar progress in a course.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    course_key = CourseKeyField(max_length=255, db_index=True)
    progress = models.IntegerField(default=0)
###########
########### send email
from openedx.core.djangoapps.ace_common.message import BaseMessageType
from openedx.core.djangoapps.ace_common.template_context import get_base_template_context
class UserCourseProgressEmail(BaseMessageType):
    """
    Message Type Class for User Activation
    """
    APP_LABEL = 'user_course_progress_email'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.options['transactional'] = True

@shared_task
def send_user_course_progress_email(current_progress, progress_milestone_crossed, course_key, full_name):
    """
    Sends User Activation Code Via Email
    """
    site = Site.objects.first() or Site.objects.get_current()
    message_context = get_base_template_context(site)
    context={
            'current_progress': current_progress,
            'progress_milestone_crossed': progress_milestone_crossed,
            'course_key': course_key,
            'platform_name': "sdaia",
            'course_name': course_key.display_name,
        }
    message_context.update(context)
    try:
        msg = UserCourseProgressEmail(context=message_context).personalize(
            recipient=Recipient(0, recipient),
            language=settings.LANGUAGE_CODE,
            user_context={'full_name': full_name}
        )
        log.info(f'message_context: {message_context}')
        log.info(f'msg: {msg}')
        ace.send(msg)
        log.info('Proctoring requirements email sent to user:')
        return True
    except Exception:  # pylint: disable=broad-except
        log.exception('Could not send email for proctoring requirements to user')
        return False
###############

def get_user_course_progress(user, course_key):
    """
    Function to get the user's course completion percentage in a course.

    :param user: The user object.
    :param course_key: The course key (e.g., CourseKey.from_string("edX/DemoX/Demo_Course")).
    :return: completion percentage.
    """
    completion_summary = get_course_blocks_completion_summary(course_key, user)
    logger.info(f"\n completion_summary: {completion_summary}")
    
    complete_count = completion_summary.get('complete_count', 0)
    incomplete_count = completion_summary.get('incomplete_count', 0)
    locked_count = completion_summary.get('locked_count', 0)
    total_count = complete_count + incomplete_count + locked_count
    
    completion_percentage = (complete_count / total_count) * 100
    return completion_percentage


class Command(BaseCommand):
    """ Send email to user at different progresses for a course """
    help = 'Generate courses on studio from a json list of courses'

    def add_arguments(self, parser):
        parser.add_argument(
            '--skip-archived',
            default=True,
            help="If set to False, it'll send emails for archived courses also",
        )

    def handle(self, *args, **options):
        skip_archived = options.get('skip-archived')
        
        course_ids = [course.id for course in modulestore().get_courses()]
        logger.info(f"\n course_ids: {course_ids}")

        for course_key in course_ids:
            course = modulestore().get_course(course_key)

            course_completion_percentages_for_emails = course.course_completion_percentages_for_emails
            if not course.allow_course_completion_emails or not course_completion_percentages_for_emails:
                continue

            course_completion_percentages_for_emails = course_completion_percentages_for_emails.split(",")
            try:
                course_completion_percentages_for_emails = [int(entry.strip()) for entry in course_completion_percentages_for_emails]
                logger.info(f"\n course_completion_percentages_for_emails: {course_completion_percentages_for_emails}")
            except Exception as e:
                log.info(f"invalid course_completion_percentages_for_emails for course {CourseKey.from_string(course_key)}")
                continue

            if skip_archived and course.has_ended():
                continue

            user_ids = CourseEnrollment.objects.filter(course_id=course_key, is_active=True).values_list('user_id', flat=True)
            users = User.objects.filter(id__in=user_ids)
            if not user_ids:
                continue

            for user in users:
                user_completion_percentage = get_user_course_progress(user, course_key)
                user_completion_progress_email_history, _ = CourseCompletionEmailHistory.objects.get_or_create(user=user, course_key=course_key)
                progress_last_email_sent_at = user_completion_progress_email_history and user_completion_progress_email_history.progress

                if user_completion_percentage > progress_last_email_sent_at:
                    for course_completion_percentages_for_email in course_completion_percentages_for_emails:
                        if user_completion_percentage >= course_completion_percentages_for_email > progress_last_email_sent_at:
                            is_email_sent = send_user_course_progress_email.delay(user_completion_percentage, progress_last_email_sent_at, str(course_key), user.profile.name)
                            if is_email_sent:
                                user_completion_progress_email_history.progress = course_completion_percentages_for_email
                                user_completion_progress_email_history.save()
