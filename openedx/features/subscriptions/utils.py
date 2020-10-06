from courseware.access_utils import ACCESS_DENIED, ACCESS_GRANTED
from openedx.features.subscriptions.models import UserSubscription

from student.models import User
from enrollment import api
from enrollment.data import get_course_enrollment

import logging

logger = logging.getLogger(__name__)


def track_subscription_enrollment(subscription_id, user, course_id):
    """
    Add user enrollment to valid subscription.
    """
    logger.warning('subscription id is %s', subscription_id)
    logger.warning('user id is %s', user)
    logger.warning('course_id id is %s', str(course_id))

    if subscription_id:
        enrollment = api.get_enrollment(user.username, course_id)
        valid_user_subscription = UserSubscription.get_valid_subscriptions(user.id).first()
        logger.warning('enrollment id is %s', str(enrollment.__dict__))
        logger.warning('user subscription is %s', str(valid_user_subscription.__dict__))
        if valid_user_subscription and valid_user_subscription.subscription_id == subscription_id:
            valid_user_subscription.course_enrollments.add(enrollment)

def is_course_accessible_with_subscription(user, course):
    """
    Check if user has access to a course enrolled through subscription.
    """
    course_enrolled_subscriptions = UserSubscription.objects.filter(user=user, course_enrollments__course__id=course.id)
    if not course_enrolled_subscriptions:
        return ACCESS_GRANTED

    for subscription in course_enrolled_subscriptions:
        if subscription.is_active:
            return ACCESS_GRANTED

    return ACCESS_DENIED
