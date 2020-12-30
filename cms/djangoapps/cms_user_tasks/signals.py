"""
Receivers of signals sent from django-user-tasks
"""
from __future__ import absolute_import, print_function, unicode_literals

from crum import CurrentRequestUserMiddleware
import logging
from django.conf import settings

from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers
from django.urls import reverse
from django.dispatch import receiver
from user_tasks.models import UserTaskArtifact
from user_tasks.signals import user_task_stopped

from six.moves.urllib.parse import urljoin  # pylint: disable=import-error

from openedx.core.lib.celery.task_utils import emulate_http_request
from .tasks import send_task_complete_email

LOGGER = logging.getLogger(__name__)


@receiver(user_task_stopped, dispatch_uid="cms_user_task_stopped")
def user_task_stopped_handler(sender, **kwargs):  # pylint: disable=unused-argument
    """
    Handles sending notifications when a django-user-tasks completes.
    This is a signal receiver for user_task_stopped. Currently it only sends
    a generic "task completed" email, and only when a top-level task
    completes. Eventually it might make more sense to create specific per-task
    handlers.
    Arguments:
        sender (obj): Currently the UserTaskStatus object class
        **kwargs: See below
    Keywork Arguments:
        status (obj): UserTaskStatus of the completed task
    Returns:
        None
    """
    status = kwargs['status']

    # Only send email when the entire task is complete, should only send when
    # a chain / chord / etc completes, not on sub-tasks.
    if status.parent is None:
        # `name` and `status` are not unique, first is our best guess
        artifact = UserTaskArtifact.objects.filter(status=status, name="BASE_URL").first()

        detail_url = None
        if artifact and artifact.url.startswith(('http://', 'https://')):
            detail_url = urljoin(
                artifact.url,
                reverse('usertaskstatus-detail', args=[status.uuid])
            )

        try:
            disable_emails = configuration_helpers.get_value(
                'DISABLE_CMS_TASK_EMAILS',
                settings.FEATURES.get('DISABLE_CMS_TASK_EMAILS', True)
            )
            LOGGER.info('Settings Features: {}'.format(disable_emails))
            LOGGER.info('from address: {}'.format(configuration_helpers.get_value('email_from_address')))
            LOGGER.info('configurations enabled: {}'.format(configuration_helpers.is_site_configuration_enabled()))
            # Need to str state_text here because it is a proxy object and won't serialize correctly
            send_task_complete_email.delay(
                status.name.lower(),
                str(status.state_text),
                status.user.email,
                detail_url,
                disable_emails,
            )
        except Exception:  # pylint: disable=broad-except
            LOGGER.exception("Unable to queue send_task_complete_email")
