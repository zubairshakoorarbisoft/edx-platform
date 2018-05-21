"""
ACE message types for the student module.
"""

from openedx.core.djangoapps.ace_common.message import ACEMessageType


class PasswordReset(ACEMessageType):
    def __init__(self, *args, **kwargs):
        super(PasswordReset, self).__init__(*args, **kwargs)

        self.options['transactional'] = True
