"""
Django admin command to update user credits on the basis of earned certificates.
"""

from django.core.management.base import BaseCommand

from lms.djangoapps.certificates.models import GeneratedCertificate
from openedx.features.clearesult_features.credits.utils import gennerate_user_course_credits


class Command(BaseCommand):
    """
    This command attempts to update users earned credits.
    Example usage:
        $ ./manage.py lms gennerate_user_course_credits
    """
    help = 'Command to update user earned credits on the basis of earned certificates'

    def handle(self, *args, **options):
        for certificate in GeneratedCertificate.objects.all():
            gennerate_user_course_credits(certificate.course_id, certificate.user)
