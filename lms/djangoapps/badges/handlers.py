"""
Badges related signal handlers.
"""


from django.dispatch import receiver
from django.db.models import F
from django.db.models.signals import post_save

from common.djangoapps.student.models import EnrollStatusChange
from common.djangoapps.student.signals import ENROLL_STATUS_CHANGE
from lms.djangoapps.badges.events.course_meta import award_enrollment_badge
from lms.djangoapps.badges.models import BadgeAssertion, LeaderboardConfiguration, LeaderboardEntry
from lms.djangoapps.badges.utils import badges_enabled, calculate_score
from lms.djangoapps.badges.tasks import update_leaderboard_enties


@receiver(ENROLL_STATUS_CHANGE)
def award_badge_on_enrollment(sender, event=None, user=None, **kwargs):  # pylint: disable=unused-argument
    """
    Awards enrollment badge to the given user on new enrollments.
    """
    if badges_enabled and event == EnrollStatusChange.enroll:
        award_enrollment_badge(user)


@receiver(post_save, sender=BadgeAssertion)
def update_leaderboard_entry(sender, instance, created, **kwargs):
    """
    Update or create a leaderboard entry when a BadgeAssertion is created.
    """
    if created:
        user = instance.user
        issuing_component = instance.badge_class.issuing_component

        course_badge_score, event_badge_score = LeaderboardConfiguration.get_current_or_default_values()

        leaderboard_entry, created = LeaderboardEntry.objects.get_or_create(user=user)
        leaderboard_entry.badge_count += 1
        leaderboard_entry.event_badge_count += int(issuing_component == 'openedx__course')
        leaderboard_entry.course_badge_count += int(issuing_component == '')

        leaderboard_entry.score = calculate_score(
            course_badge_score,
            event_badge_score,
            leaderboard_entry.course_badge_count,
            leaderboard_entry.event_badge_count
        )

        leaderboard_entry.save()


@receiver(post_save, sender=LeaderboardConfiguration)
def update_leaderboard_scores(sender, instance, **kwargs):
    """
    Update scores for all entries when LeaderboardConfiguration is updated
    Intiate a Celery task as the update could be time intensive.
    """
    course_badge_score, event_badge_score = instance.course_badge_score, instance.event_badge_score
    if not instance.enabled:
        course_badge_score, event_badge_score = instance.COURSE_BADGE_SCORE, instance.EVENT_BADGE_SCORE
    
    update_leaderboard_enties.delay(course_badge_score, event_badge_score)
