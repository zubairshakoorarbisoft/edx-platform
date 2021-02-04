import logging
import requests
import six

from celery import task
from django.conf import settings


log = logging.getLogger('edx.celery.task')

@task()
def call_drupal_logout_endpoint(email):
    api_credentials = getattr(settings, 'DRUPAL_LOGOUT_API_CREDENTIALS', {})
    if api_credentials == {}:
        log.info('You have not provided drupal logout API credentials.')
        return

    url = api_credentials.get('url', '') + email
    username = api_credentials.get('username', '')
    password = api_credentials.get('password', '')

    response = requests.get(url, auth=(username, password))

    if response.status_code == 200:
        log.info('Success: User with email {} has been successfully logged out from Drupal.'.format(email))
    else:
        log.info('Failed: User with email {} has not been logged out from Drupal.'.format(email))
