"""
Signals for clearesult features django app.
"""
from logging import getLogger

from completion.models import BlockCompletion
from django.conf import settings
from django.contrib.auth.models import User
from django.dispatch import receiver
from django.db.models.signals import post_save

from course_modes.models import CourseMode
from lms.djangoapps.verify_student.models import ManualVerification
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from openedx.core.djangoapps.site_configuration.models import SiteConfiguration
from student.models import UserProfile
from openedx.core.djangoapps.signals.signals import COURSE_GRADE_NOW_PASSED, COURSE_GRADE_NOW_FAILED
from openedx.features.clearesult_features.models import (
    ClearesultCourseCompletion, ClearesultGroupLinkage,
    ClearesultSiteConfiguration
)
from openedx.features.clearesult_features.credits.utils import (
    generate_user_course_credits,
    remove_user_cousre_credits_if_exist,
)
from openedx.features.clearesult_features.utils import (
    generate_clearesult_course_completion,
    update_clearesult_course_completion,
    is_course_graded, is_lms_site
)
from openedx.features.clearesult_features.tasks import check_and_enroll_group_users_to_mandatory_courses

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
def genrate_user_course_credits_and_course_completion(sender, user, course_id, **kwargs):  # pylint: disable=unused-argument
    """
    Listen for a learner passing a course and update user credits and completion dates.
    """
    generate_user_course_credits(course_id, user)
    generate_clearesult_course_completion(user, course_id)


@receiver(COURSE_GRADE_NOW_FAILED)
def remove_user_cousre_credits_and_update_course_completion(sender, user, course_id, **kwargs):  # pylint: disable=unused-argument
    """
    Listen for a learner failing a course and update user credits and completion dates.
    """
    remove_user_cousre_credits_if_exist(course_id, user)
    update_clearesult_course_completion(user, course_id)


@receiver(post_save, sender=BlockCompletion)
def set_clearesult_course_completion(sender, instance, created, **kwargs):
    """
    Listen for block completion and update clearesult course completion.

    On each save of BlockCompletion save on ClearesultCourseCompletion as well.
    For graded courses don't mess up with the pass date. But for non graded courses
    pass date will be same as of completion date.
    """
    if created:
        if is_course_graded(instance.context_key, instance.user):
            defaults = {
                'completion_date':instance.created,
            }
        else:
            defaults = {
                'completion_date':instance.created,
                'pass_date': instance.created
            }

        ClearesultCourseCompletion.objects.update_or_create(
            user=instance.user, course_id=instance.context_key,
            defaults=defaults
        )

@receiver(post_save, sender=SiteConfiguration)
def create_default_group(sender, instance, created, **kwargs):
    """
    Listen for SiteConfiguration and create default site group on new site creation.
    """
    if is_lms_site(instance.site):
        clearesult_configuration = ClearesultSiteConfiguration.current(instance.site)

        if clearesult_configuration:
            # check if default group is set for the site
            try:
                if not clearesult_configuration.default_group:
                    raise ClearesultGroupLinkage.DoesNotExist
            except ClearesultGroupLinkage.DoesNotExist:
                # if default group is not set then get or create DEFAULT group for the site and set it
                # as default group
                default_site_group = ClearesultGroupLinkage.objects.get_or_create(
                    name=settings.SITE_DEFAULT_GROUP_NAME,
                    site=instance.site
                )
                clearesult_configuration.default_group = default_site_group[0]
                clearesult_configuration.save()
        else:
            default_site_group = ClearesultGroupLinkage.objects.get_or_create(
                    name=settings.SITE_DEFAULT_GROUP_NAME,
                    site=instance.site
            )
            clearesult_configuration.objects.create(
                site=instance.site, default_group=default_site_group[0], security_code_required=False, enabled=True
            )
