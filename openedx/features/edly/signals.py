from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from lms.djangoapps.instructor.enrollment import get_email_params
from openedx.features.edly.tasks import send_course_enrollment_mail
from student.models import CourseEnrollment


@receiver(post_save, sender=CourseEnrollment)
def handle_user_enroll(sender, instance, **kwargs):
    """

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
