"""
Signals for clearesult features django app.
"""
from logging import getLogger

from django.conf import settings
from django.dispatch import receiver
from django.db.models.signals import post_save

from course_modes.models import CourseMode
from lms.djangoapps.verify_student.models import ManualVerification
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from student.models import UserProfile
from openedx.core.djangoapps.signals.signals import (
    COURSE_GRADE_NOW_PASSED,
    COURSE_GRADE_CHANGED
)
from openedx.features.clearesult_features.credits.utils import gennerate_user_course_credits
from openedx.features.clearesult_features.models import (
    ClearesultCourseCredit,
    ClearesultCreditProvider,
    UserCreditsProfile
)

logger = getLogger(__name__)


@receiver(post_save, sender=CourseOverview)
def create_default_course_mode(sender, instance, created, **kwargs):
    if not (settings.FEATURES.get('ENABLE_DEFAULT_COURSE_MODE_CREATION') and created):
        logger.info('Flag is not set - Skip Auto creation of default course mode.')
        return

    default_mode_slug = settings.COURSE_MODE_DEFAULTS['slug']
    if default_mode_slug != "audit":
        logger.info('Generating Default Course mode: {}'.format(default_mode_slug))
        course_mode = CourseMode(
            course=instance,
            mode_slug=default_mode_slug,
            mode_display_name=settings.COURSE_MODE_DEFAULTS['name'],
            min_price=settings.COURSE_MODE_DEFAULTS['min_price'],
            currency=settings.COURSE_MODE_DEFAULTS['currency'],
            expiration_date=settings.COURSE_MODE_DEFAULTS['expiration_datetime'],
            description=settings.COURSE_MODE_DEFAULTS['description'],
            sku=settings.COURSE_MODE_DEFAULTS['sku'],
            bulk_sku=settings.COURSE_MODE_DEFAULTS['bulk_sku'],
        )
        course_mode.save()
    else:
        logger.info('No need to generate Course mode for Audit mode.')


@receiver(post_save, sender=UserProfile)
def generate_manual_verification_for_user(sender, instance, created, **kwargs):
    """
    Generate ManualVerification for the User (whose UserProfile instance has been created).
    """
    if not (settings.FEATURES.get('ENABLE_AUTOMATIC_ACCOUNT_VERIFICATION') and created):
        return

    logger.info('Generating ManualVerification for user: {}'.format(instance.user.email))
    try:
        ManualVerification.objects.create(
            user=instance.user,
            status='approved',
            reason='SKIP_IDENTITY_VERIFICATION',
            name=instance.name
        )
    except Exception:  # pylint: disable=broad-except
        logger.error('Error while generating ManualVerification for user: %s', instance.user.email, exc_info=True)


@receiver(COURSE_GRADE_NOW_PASSED)
def genrate_user_credits(sender, user, course_id, **kwargs):  # pylint: disable=unused-argument
    """
    Listen for a learner passing a course, update user credits.
    """
    gennerate_user_course_credits(course_id, user)
