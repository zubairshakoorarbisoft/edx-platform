import logging

import requests

from openedx.core.djangoapps.credit.exceptions import RequestAlreadyCompleted, CreditProviderNotConfigured
from openedx.core.djangoapps.credit.models import CreditRequest
from openedx.core.djangoapps.credit.signature import signature, get_shared_secret_key

log = logging.getLogger(__name__)

CREDIT_REQUEST_ID = 230

credit_request = CreditRequest.objects.get(id=CREDIT_REQUEST_ID)
credit_provider = credit_request.provider
credit_provider_url = credit_provider.provider_url
shared_secret_key = get_shared_secret_key(credit_provider.provider_id)

if not shared_secret_key:
    msg = 'Credit provider with ID [{id}] does not have a secret key configured.'.format(id=credit_provider.provider_id)
    log.error(msg)
    raise CreditProviderNotConfigured(msg)

if not credit_provider_url:
    msg = 'Credit provider [{id}] does not support this integration.'.format(id=credit_provider.provider_id)
    log.error(msg)
    raise CreditProviderNotConfigured(msg)

if credit_request.status != CreditRequest.REQUEST_STATUS_PENDING:
    msg = 'Credit request [{id}] is in the {status} state. Only pending requests can be re-sent.'.format(
        id=credit_request.id, status=credit_request.status
    )
    log.error(msg)
    raise RequestAlreadyCompleted(msg)

parameters = credit_request.parameters
parameters['signature'] = signature(parameters, shared_secret_key)

response = requests.post(credit_provider_url, data=parameters)

if response.status_code > 299:
    log.error('Failed to re-send credit request [%d]. HTTP status code was [%d}',
              credit_request.id, response.status_code)
else:
    log.info('Successfully re-sent credit request [%d]. HTTP status code was [%d}',
             credit_request.id, response.status_code)

log.info('Response body for re-sent credit request [%d]:\n\n%s',
         credit_request.id, response.content)

print(response.status_code)
print(response.content)
