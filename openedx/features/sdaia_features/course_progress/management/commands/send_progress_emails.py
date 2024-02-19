"""
Django admin command to send message email emails.
"""
from logging import getLogger
from django.core.management.base import BaseCommand

log = getLogger(__name__)

class Command(BaseCommand):
    """
    This command will update users about their course progress.
        $ ./manage.py lms send_progress_emails
    """
    help = 'Command to update users about their course progress'

    def handle(self, *args, **options):
        print("Hello")
