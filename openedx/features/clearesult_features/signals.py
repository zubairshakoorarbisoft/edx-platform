"""
Signals for clearesult features django app.
"""
import io
from csv import DictReader, DictWriter, Error, Sniffer, reader
from logging import getLogger

from django.conf import settings
from django.contrib.auth.models import User
from django.db import IntegrityError, transaction
from django.dispatch import receiver
from django.db.models.signals import post_save
from django.utils.crypto import get_random_string
from social_django.models import UserSocialAuth

from course_modes.models import CourseMode
from lms.djangoapps.verify_student.models import ManualVerification
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from openedx.features.clearesult_features.models import (
    ClearesultUsersImport, ClearesultUserProfile,
    UserCreditsProfile, ClearesultCreditProvider
)
from openedx.features.clearesult_features.utils import get_file_encoding
from openedx.features.clearesult_features.credits.utils import get_credit_provider_by_short_code
from openedx.features.clearesult_features.auth_backend import ClearesultAzureADOAuth2
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
CREATION_SUCCESSFUL = 'CREATED'
CREATION_FAILED = 'FAILED'
UPDATION_SUCCESSFUL = 'UPDATED'


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


@receiver(post_save, sender=ClearesultUsersImport)
def create_users_from_csv_file(sender, instance, created, **kwargs):
    """
    Reads data from CSV file and creates users and their profiles according to the
    details given in the file. Also writes the output status in the file.
    """
    file_controller = _get_file_control(instance.user_accounts_file.path)
    if not file_controller:
        logger.info('Unable to get file control.')
        return

    output_file_rows = []
    try:
        for row in file_controller['csv_reader']:
            row['Status'] = ''
            row['Error'] = ''
            try:
                with transaction.atomic():
                    edx_user = _create_or_update_edx_users(row)
                    _create_or_update_edx_user_profile(edx_user, row)
                    _create_or_update_clearesult_user_profile(edx_user, row)
                    _create_or_update_user_credits_profile(edx_user, row)
                    _create_or_update_user_social_auth_accounts(edx_user)
            except IntegrityError as error:
                logger.exception('Error while creating/updating ({}) user and its '
                                 'profiles with the following errors {}.'.format(row.get('Email'), error))
                row['status'] = CREATION_FAILED
                row['error'] = error
            output_file_rows.append(row)
    except Error as err:
        logger.exception('Error while traversing {} file content with following error {}.'
                         .format(instance.user_accounts_file.path, err))
    file_controller['csv_file'].close()
    _write_status_on_csv_file(instance.user_accounts_file.path, output_file_rows)


def _create_or_update_edx_users(user_info):
    """
    Creates/updates the edx users.

    Arguements:
        user_info (dict): Dict containing the values of single row of csv file
    """
    user_data = {
        'email': user_info.get('Email'),
        'first_name': user_info.get('First Name'),
        'last_name': user_info.get('Last Name'),
        'username': user_info.get('Username'),
        'is_active': True
    }
    edx_user, created = User.objects.update_or_create(username=user_info.get('Username'), defaults=user_data)
    if created:
        edx_user.set_password(get_random_string())
        edx_user.save()
        logger.info('{} user has been created.'.format(edx_user.username))
    else:
        logger.info('{} user has been updated.'.format(edx_user.username))

    return edx_user


def _create_or_update_edx_user_profile(edx_user, user_info):
    """
    Creates/updates the edx user profile.

    Arguements:
        edx_user (User): Django User
        user_info (dict): Dict containing the values of single row of csv file
    """
    profile_data = {
        'name': '{} {}'.format(edx_user.first_name, edx_user.last_name),
        'city': user_info.get('City'),
        'location': user_info.get('Street Address'),
        'phone_number': user_info.get('Primary Phone')
    }
    _, created = UserProfile.objects.update_or_create(user=edx_user, defaults=profile_data)
    if created:
        logger.info('{} edx profile has been created.'.format(edx_user.username))
    else:
        logger.info('{} edx profile has been updated.'.format(edx_user.username))


def _create_or_update_clearesult_user_profile(edx_user, user_info):
    """
    Creates/updates the clearesult user profile.

    Arguements:
        edx_user (User): Django User
        user_info (dict): Dict containing the values of single row of csv file
    """
    clearesult_profile_data = {
        'job_title': user_info.get('Job Title'),
        'company': user_info.get('Company'),
        'state_or_province': user_info.get('State/Province'),
        'postal_code': user_info.get('Postal Code')
    }
    _, created = ClearesultUserProfile.objects.update_or_create(user=edx_user, defaults=clearesult_profile_data)
    if created:
        logger.info('{} clearesult profile has been created.'.format(edx_user.username))
        user_info['status'] = CREATION_SUCCESSFUL
    else:
        logger.info('{} clearesult profile has been updated.'.format(edx_user.username))
        user_info['status'] = UPDATION_SUCCESSFUL


def _create_or_update_user_credits_profile(edx_user, user_info):
    """
    Creates/updates the user credits profile.

    Performs operation only for those users who have some distinct value of
    continueing education ID for the credit providers available in the platform.

    Arguements:
        edx_user (User): Django User
        user_info (dict): Dict containing the values of single row of csv file
    """
    possible_credit_providers = getattr(settings, 'CLEARESULT_CREDIT_PROVIDERS', [])

    for possible_credit_provider in possible_credit_providers:
        if possible_credit_provider in user_info.keys() and not user_info.get(possible_credit_provider) == '':
            credit_provider = get_credit_provider_by_short_code(possible_credit_provider)
            if credit_provider:
                data = {
                    'credit_id': user_info.get(possible_credit_provider)
                }
                _, created = UserCreditsProfile.objects.update_or_create(user=edx_user,
                                                                         credit_type=credit_provider,
                                                                         defaults=data)
                if created:
                    logger.info('{} account ID for {} credit provider of user {} has been added.'.format(
                        user_info.get(possible_credit_provider),
                        possible_credit_provider,
                        edx_user.email
                    ))
                else:
                    logger.info('{} account ID for {} credit provider of user {} has been updated.'.format(
                        user_info.get(possible_credit_provider),
                        possible_credit_provider,
                        edx_user.email
                    ))


def _create_or_update_user_social_auth_accounts(edx_user):
    """
    Creates/updates the social auth accounts of the given edx users.

    Arguements:
        edx_user (User): Django User
    """
    data = {
        'uid': edx_user.email,
        'provider': ClearesultAzureADOAuth2.name,
        'user': edx_user
    }
    _, created = UserSocialAuth.objects.update_or_create(user=edx_user, provider=ClearesultAzureADOAuth2.name,
                                                         defaults=data)

    if created:
        logger.info('User socail auth for user {} has been created.'.format(edx_user.email))
    else:
        logger.info('User socail auth for user {} has been updated.'.format(edx_user.email))


def _get_file_control(file_path):
    """
    Returns opened file and dict_reader object of the given file path.
    """
    csv_file = None
    dialect = None
    try:
        encoding = get_file_encoding(file_path)
        if not encoding:
            logger.exception('Because of invlid file encoding format, user creation process is aborted.')
            return

        csv_file = io.open(file_path, 'r', encoding=encoding)
        try:
            dialect = Sniffer().sniff(csv_file.readline())
        except Error:
            logger.exception('Could not determine delimiter in the file.')
            csv_file.close()
            return

        csv_file.seek(0)
    except IOError as error:
        logger.exception('({}) --- {}'.format(error.filename, error.strerror))
        return

    dict_reader = DictReader(csv_file, delimiter=dialect.delimiter if dialect else ',')
    csv_reader = (dict((k.strip(), v.strip() if v else v) for k, v in row.items()) for row in dict_reader)

    return {'csv_file': csv_file, 'csv_reader': csv_reader}


def _write_status_on_csv_file(file_path, output_file_rows):
    """
    Writes the output data on the given file.
    """
    try:
        with open(file_path, 'w') as csv_file:
            if output_file_rows:
                writer = DictWriter(csv_file, fieldnames=output_file_rows[0].keys())
                writer.writeheader()
                for row in output_file_rows:
                    writer.writerow(row)
    except IOError as error:
        logger.exception('(file_path) --- {}'.format(file_path, error.strerror))
