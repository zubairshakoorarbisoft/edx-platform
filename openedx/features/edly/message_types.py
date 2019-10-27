from openedx.core.djangoapps.ace_common.message import BaseMessageType


class OutlineChangeNotification(BaseMessageType):
    """
    A message for notifying user about new changes in the course outline.
    """
    pass


class HandoutChangeNotification(BaseMessageType):
    """
    A message for notifying user about new changes in the course handouts.
    """
    pass
