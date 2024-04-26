import logging
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db.models import Sum, Case, When, Value, IntegerField, Count
from lms.djangoapps.badges.utils import calculate_score
from lms.djangoapps.badges.models import BadgeAssertion, LeaderboardConfiguration, LeaderboardEntry

logger = logging.getLogger(__name__)  # pylint: disable=invalid-name
User = get_user_model()


class Command(BaseCommand):
    """
    Command to populate or update leaderboard entries
    Example:
        ./manage.py lms update_leaderboard
    """
    help = 'Populate or update leaderboard entries'

    def get_leaderboard_data(self):
        """
        Get leaderboard data from BadgeAssertion model.

        Returns:
            QuerySet: A queryset containing aggregated leaderboard data.
        """
        leaderboard_data = (
            BadgeAssertion.objects
            .values('user__id', 'badge_class__issuing_component')
            .annotate(
                is_course_badge=Case(
                    When(badge_class__issuing_component='', then=Value(1)),
                    default=Value(0),
                    output_field=IntegerField()
                ),
                is_event_badge=Case(
                    When(badge_class__issuing_component='openedx__course', then=Value(1)),
                    default=Value(0),
                    output_field=IntegerField()
                )
            ).values('user__id')
            .annotate(badge_count=Count('id'), course_badge_count=Sum('is_course_badge'), event_badge_count=Sum('is_event_badge'))
        )

        return leaderboard_data

    def populate_or_update_leaderboard_entries(self):
        """
        Populate or create leaderboard entries based on BadgeAssertion data.
        """
        leaderboard_data = self.get_leaderboard_data()
        course_badge_score, event_badge_score = LeaderboardConfiguration.get_current_or_default_values()

        for entry in leaderboard_data:
            user_id = entry['user__id']
            score = calculate_score(course_badge_score, event_badge_score, entry['course_badge_count'], entry['event_badge_count'])

            LeaderboardEntry.objects.update_or_create(
                user_id=user_id,
                badge_count=entry['badge_count'],
                course_badge_count=entry['course_badge_count'],
                event_badge_count=entry['event_badge_count'],
                score=score,
            )

    def handle(self, *args, **options):
        self.populate_or_update_leaderboard_entries()
        logger.info('Successfully updated leaderboard entries')
