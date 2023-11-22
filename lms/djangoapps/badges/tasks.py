"""
Defines asynchronous celery task for updateing leaderboard entries
"""
import logging

from django.db.models import F
from celery import shared_task
from celery_utils.logged_task import LoggedTask
from edx_django_utils.monitoring import set_code_owner_attribute
from lms.djangoapps.badges.models import BadgeAssertion, LeaderboardConfiguration, LeaderboardEntry


log = logging.getLogger(__name__)


@shared_task(base=LoggedTask)
@set_code_owner_attribute
def update_leaderboard_enties(course_badge_score, event_badge_score):
    """
    Bulk Update scores for all entries in the LeaderboardEntry
    """
    leaderboard_entries = LeaderboardEntry.objects.all()
    leaderboard_entries.update(
        score=F('course_badge_count') * course_badge_score + F('event_badge_count') * event_badge_score
    )
    log.info(
        f"Updated {leaderboard_entries.count()} enties in the LeaderboardEntry table"
    )
