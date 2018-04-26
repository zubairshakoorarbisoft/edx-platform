"""
Implementation of abstraction layer for other parts of the system to make queries related to ID Verification.
"""

import logging

from itertools import chain
from django.conf import settings
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext as _

from course_modes.models import CourseMode
from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers
from student.models import User

from .models import SoftwareSecurePhotoVerification, SSOVerification
from .utils import earliest_allowed_verification_date

log = logging.getLogger(__name__)


class XBlockVerificationService(object):
    """
    Learner verification XBlock service.
    """

    def get_status(self, user_id):
        """
        Returns the user's current photo verification status.

        Args:
            user_id: the user's id

        Returns: one of the following strings
            'none' - no such verification exists
            'expired' - verification has expired
            'approved' - verification has been approved
            'pending' - verification process is still ongoing
            'must_reverify' - verification has been denied and user must resubmit photos
        """
        user = User.objects.get(id=user_id)
        return IDVerificationService.user_status(user)

    def reverify_url(self):
        """
        Returns the URL for a user to verify themselves.
        """
        return reverse('verify_student_reverify')


class IDVerificationService(object):
    """
    Learner verification service interface for callers within edx-platform.
    """

    @classmethod
    def user_is_verified(cls, user, earliest_allowed_date=None):
        """
        Return whether or not a user has satisfactorily proved their identity.
        Depending on the policy, this can expire after some period of time, so
        a user might have to renew periodically.

        This will check for the user's *initial* verification.
        """
        filter_kwargs = {
            'user': user,
            'status': 'approved',
            'created_at__gte': (earliest_allowed_date or earliest_allowed_verification_date())
        }

        return (SoftwareSecurePhotoVerification.objects.filter(**filter_kwargs).exists() or
                SSOVerification.objects.filter(**filter_kwargs).exists())

    @classmethod
    def verifications_for_user(cls, user):
        """
        Return a query set for all records associated with the given user.
        return chain of photo and sso verifications
        """
        return chain(SoftwareSecurePhotoVerification.objects.filter(user=user),
                     SSOVerification.objects.filter(user=user))

    @classmethod
    def get_verified_users(cls, users):
        """
        Return the list of user ids that have non expired verifications from the given list of users.
        return list of users that have either type of record
        """
        filter_kwargs = {
            'user__in': users,
            'status': 'approved',
            'created_at__gte': (earliest_allowed_verification_date())
        }
        return chain(
            SoftwareSecurePhotoVerification.objects.filter(**filter_kwargs).select_related('user'),
            SSOVerification.objects.filter(**filter_kwargs).select_related('user')
        )

    @classmethod
    def get_expiration_datetime(cls, user, statuses):
        """
        Check whether the user has an approved verification and return the
        "expiration_datetime" of most recent "approved" verification.

        Arguments:
            user (Object): User
            queryset: If a queryset is provided, that will be used instead
                of hitting the database.

        Returns:
            expiration_datetime: expiration_datetime of most recent "approved"
            verification.

        add a status parameter to filter on
        check both records and return expiration_datetime of most recent one
        """
        filter_kwargs = {
            'user': user,
            'status__in': statuses,
        }

        photo_id_verifications = SoftwareSecurePhotoVerification.objects.filter(**filter_kwargs)
        sso_id_verifications = SSOVerification.objects.filter(**filter_kwargs)

        photo_id_verification = photo_id_verifications and photo_id_verifications.first()
        sso_id_verification = sso_id_verifications and sso_id_verifications.first()

        if not photo_id_verification and not sso_id_verification:
            return None
        elif photo_id_verification and not sso_id_verification:
            return photo_id_verification.expiration_datetime
        elif sso_id_verification and not photo_id_verification:
            return sso_id_verification.expiration_datetime
        elif photo_id_verification.created_at > sso_id_verification.created_at:
            return photo_id_verification.expiration_datetime
        else:
            return sso_id_verification.expiration_datetime

    @classmethod
    def user_has_valid_or_pending(cls, user):
        """
        Check whether the user has an active or pending verification attempt

        Returns:
            bool: True or False according to existence of valid verifications
        """
        filter_kwargs = {
            'user': user,
            'status__in': ['submitted', 'approved', 'must_retry'],
            'created_at__gte': earliest_allowed_verification_date()
        }

        return (SoftwareSecurePhotoVerification.objects.filter(**filter_kwargs).exists() or
                SSOVerification.objects.filter(**filter_kwargs).exists())

    @classmethod
    def user_status(cls, user):
        """
        Returns the status of the user based on their past verification attempts, and any corresponding error messages.

        If no such verification exists, returns 'none'
        If verification has expired, returns 'expired'
        If the verification has been approved, returns 'approved'
        If the verification process is still ongoing, returns 'pending'
        If the verification has been denied and the user must resubmit photos, returns 'must_reverify'

        This checks most recent verification
        """
        # should_display only refers to displaying the verification attempt status to a user
        # once a verification attempt has been made, otherwise we will display a prompt to complete ID verification.
        user_status = {
            'status': 'none',
            'error': '',
            'should_display': True,
        }

        # We need to check the user's most recent attempt.
        try:
            photo_id_verifications = SoftwareSecurePhotoVerification.objects.filter(user=user).order_by('-updated_at')
            sso_id_verifications = SSOVerification.objects.filter(user=user).order_by('-updated_at')

            photo_id_verification = photo_id_verifications and photo_id_verifications.first()
            sso_id_verification = sso_id_verifications and sso_id_verifications.first()

            if not photo_id_verification and not sso_id_verification:
                return user_status
            elif photo_id_verification and not sso_id_verification:
                attempt = photo_id_verification
            elif sso_id_verification and not photo_id_verification:
                attempt = sso_id_verification
            elif photo_id_verification.created_at > sso_id_verification.created_at:
                attempt = photo_id_verification
            else:
                attempt = sso_id_verification
        except IndexError:
            # The user has no verification attempts, return the default set of data.
            return user_status

        user_status['should_display'] = attempt.should_display_status_to_user()
        if attempt.created_at < earliest_allowed_verification_date():
            if user_status['should_display']:
                user_status['status'] = 'expired'
                user_status['error'] = _("Your {platform_name} verification has expired.").format(
                    platform_name=configuration_helpers.get_value('platform_name', settings.PLATFORM_NAME),
                )
            else:
                # If we have a verification attempt that never would have displayed to the user,
                # and that attempt is expired, then we should treat it as if the user had never verified.
                return user_status

        # If someone is denied their original verification attempt, they can try to reverify.
        elif attempt.status == 'denied':
            user_status['status'] = 'must_reverify'
            if hasattr(attempt, 'error_msg') and attempt.error_msg:
                user_status['error'] = attempt.parsed_error_msg()

        elif attempt.status == 'approved':
            user_status['status'] = 'approved'

        elif attempt.status in ['submitted', 'approved', 'must_retry']:
            # user_has_valid_or_pending does include 'approved', but if we are
            # here, we know that the attempt is still pending
            user_status['status'] = 'pending'

        return user_status

    @classmethod
    def verification_status_for_user(cls, user, user_enrollment_mode, user_is_verified=None):
        """
        Returns the verification status for use in grade report.
        """
        if user_enrollment_mode not in CourseMode.VERIFIED_MODES:
            return 'N/A'

        if user_is_verified is None:
            user_is_verified = cls.user_is_verified(user)

        if not user_is_verified:
            return 'Not ID Verified'
        else:
            return 'ID Verified'
