"""
Base Message types to be used to construct ace messages.
"""
from django.conf import settings

from edx_ace.message import MessageType
from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers


class ACEMessageType(MessageType):
    def __init__(self, *args, **kwargs):
        super(ACEMessageType, self).__init__(*args, **kwargs)
        self.options['from_address'] = configuration_helpers.get_value(
            'email_from_address', settings.DEFAULT_FROM_EMAIL
        )
