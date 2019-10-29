from openedx.core.djangoapps.ace_common.message import BaseMessageType


class OutlineChangesNotification(BaseMessageType):
    """
    A message for notifying user about new changes in the course outline.
    """
    pass


class HandoutChangesNotification(BaseMessageType):
    """
    A message for notifying user about new changes in the course handouts.
    """
    pass
