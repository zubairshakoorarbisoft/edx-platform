from openedx.core.djangoapps.ace_common.message import BaseMessageType


class MandatoryCoursesNotification(BaseMessageType):
    """
    A message for notifying students about mandatory courses enrollment.
    """
    pass


class MandatoryCoursesApproachingDueDatesNotification(BaseMessageType):
    """
    A message for notifying Students about mandatory courses approching due date.
    """
    pass

class MandatoryCoursesPassedDueDatesNotification(BaseMessageType):
    """
    A message for notifying Admins about mandatory courses passed due dates.
    """
    pass


class CoursePassedNotification(BaseMessageType):
    """
    A message for notifying learner that he has passed a course.
    """
    pass
