from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from six import text_type

from lms.djangoapps.instructor.enrollment import get_email_params
from openedx.core.djangoapps.theming.helpers import get_current_site
from openedx.features.edly.tasks import send_course_enrollment_mail
from student.models import CourseEnrollment


@receiver(post_save, sender=CourseEnrollment)
def handle_user_enrollment(sender, instance, **kwargs):
    """
    Handle the course enrollment and send the email to the student about enrollment.

    Arguments:
        sender: Model from which we received signal.
        instance: Instance of model which has been created or updated
        kwargs: Remaining parts of signal.
    """

    # Send email notification if Enrollment signal is created/updated in LMS.
    if settings.ROOT_URLCONF == 'lms.urls':
        email_params = {}
        if instance.is_active:
            email_params['message_type'] = 'enrolled_enroll'
        elif not instance.is_active and not kwargs['created']:
            email_params['message_type'] = 'enrolled_unenroll'
        else:
            return

        site = get_current_site()
        site_id = ''
        if site:
            site_id = site.id
        email_params['site_id'] = site_id

        user_fullname = instance.user.profile.name
        user_email = instance.user.email

        email_params.update(get_email_params(instance.course, True, secure=False))
        email_params['contact_mailing_address'] = settings.CONTACT_MAILING_ADDRESS
        email_params['email_address'] = user_email
        email_params['full_name'] = user_fullname
        email_params['enroll_by_self'] = True
        email_params['course'] = text_type(email_params['course'])

        send_course_enrollment_mail.delay(user_email, email_params)
