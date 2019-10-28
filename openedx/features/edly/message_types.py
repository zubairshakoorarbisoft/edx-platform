from openedx.core.djangoapps.ace_common.message import BaseMessageType


class OutlineChangesNotification(BaseMessageType):
    """
    A message for notifying user about new changes in course.

    """
    APP_LABEL = 'edly'

    def __init__(self, *args, **kwargs):
        super(OutlineChangesNotification, self).__init__(*args, **kwargs)
        self.options['transactional'] = True


class HandoutChangesNotification(BaseMessageType):
    """
    A message for notifying user about new changes in course.

    """
    APP_LABEL = 'edly'

    def __init__(self, *args, **kwargs):
        super(HandoutChangesNotification, self).__init__(*args, **kwargs)
        self.options['transactional'] = True
