from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

from lms.djangoapps.instructor.enrollment import get_email_params
from openedx.features.edly.utils import (
    send_course_enrollment_mail,
    is_notification_configured_for_site,
    update_context_with_thread,
    update_context_with_comment
)
from openedx.features.edly.tasks import send_course_enrollment_mail
from student.models import CourseEnrollment

from openedx.features.edly.message_types import (
    CommentVoteNotification,
    ThreadCreateNotification,
    ThreadVoteNotification
)
from openedx.features.edly.tasks import send_ace_message
from django_comment_common import signals as forum_signals
from openedx.core.djangoapps.site_configuration.models import SiteConfiguration
from openedx.core.djangoapps.theming.helpers import get_current_site

@receiver(post_save, sender=CourseEnrollment)
def handle_user_enrollment(sender, instance, **kwargs):
    """
    Handle the course enrollment and send the email to the student about enrollment.

    :param sender: Model from which we received signal.
    :param instance: Instance of model which has been created or updated
    :param kwargs: Remaining parts of signal.
    """

    # This if condition check's for if the Enrollment signal is created/updated using LMS or not.
    # We are handling only lms site.

    if settings.ROOT_URLCONF == 'lms.urls':
        user_fullname = instance.user.profile.name
        user_email = instance.user.email
        email_params = get_email_params(instance.course, True, secure=False)
        email_params['email_address'] = user_email
        email_params['full_name'] = user_fullname
        email_params['enroll_by_self'] = True
        if instance.is_active:
            email_params['message_type'] = 'enrolled_enroll'
        elif not instance.is_active and not kwargs['created']:
            email_params['message_type'] = 'enrolled_unenroll'
        else:
            return
        send_course_enrollment_mail.delay(user_email, email_params)


@receiver(forum_signals.thread_created)
def send_thread_create_email_notification(sender, user, post, **kwargs):
    current_site = get_current_site()
    if not is_notification_configured_for_site(current_site, post.id):
        return
    context = {
        'site_id': current_site.id,
        'course_id': unicode(post.course_id)
    }
    update_context_with_thread(context, post)
    receipients = [user.id] #THIS NEED TO BE CHANGED
    send_ace_message.apply_async(args=[context, ThreadCreateNotification(), receipients, False])


@receiver(forum_signals.thread_voted)
def send_vote_email_notification(sender, user, post, **kwargs):
    import pdb; pdb.set_trace()
    current_site = get_current_site()
    if not is_notification_configured_for_site(current_site, post.id):
        return
    context = {
        'site_id': current_site.id,
        'course_id': unicode(post.course_id),
        'voter_name': user.username,
        'voter_email': user.email
    }
    is_comment = False
    notification_object = ThreadVoteNotification()
    receipients = [post.user_id] #########################################
    if post.type == "comment":
        is_comment = True
        update_context_with_thread(context, post.thread)
        update_context_with_comment(context,  post)
        notification_object = CommentVoteNotification()
    else:
        update_context_with_thread(context, post)
    send_ace_message.apply_async(args=[context, notification_object, receipients, is_comment])
