""" Client to handle Magento requests. """
import json
import logging
import requests
from django.conf import settings
from openedx.features.clearesult_features.magento.exceptions import MissingMagentoUserKey, InvalidMagentoResponseError

logger = logging.getLogger(__name__)


class MagentoClient(object):
    """
    Client for Paystack API requests.
    """
    _POST_METHOD = 'POST'
    _GET_METHOD = 'GET'
    _CONTENT_TYPE = 'application/json'

    def __init__(self, email):
        """
        Constructs a new instance of the Magento client.
        """
        self._BASE_API_END_POINT = settings.MAGENTO_BASE_API_URL
        self._REDIRECT_URL = settings.MAGENTO_REDIRECT_URL
        self._MAGENTO_LMS_INTEGRATION_TOKEN = settings.MAGENTO_LMS_INTEGRATION_TOKEN
        self._MAGENTO_USER_KEY = None

        self.generate_costomer_token(email)
        if not self._MAGENTO_USER_KEY:
            raise MissingMagentoUserKey("Magento Client Error: Unable to get User Key from Magento.")

    def get_url(self, path):
        """
        Creates a request URL by appending path with base end point.
        """
        url = self._BASE_API_END_POINT
        if path:
            url += path
        return url

    def get_headers(self, token=None):
        """
        Returns Request Header required to send Paystack API.
        """
        headers = { 'Content-Type': self._CONTENT_TYPE}
        if token:
            headers.update({'Authorization': 'Bearer ' + token})
        return headers

    def parse_response(self, response):
        """
        Parses and return the response.
        """
        try:
            data = response.json()
        except ValueError:
            data = None

        if response.status_code in [200, 201]:
            logger.info("Magento API returned success response: %s.", json.dumps(data))
            return True, data

        else:
            logger.error("Magento API return response with status code: %s.", response.status_code)
            logger.error("Magento API return Error response: %s.", json.dumps(data))
            return False, data

    def handle_request(self, path, method, headers=None, data=None):
        """
        Handles all Magento API calls.
        """
        if not headers:
            headers = self.get_headers()

        method_map = {
            self._GET_METHOD: requests.get,
            self._POST_METHOD: requests.post,
        }

        request = method_map.get(method)
        payload = json.dumps(data) if data else data
        url = self.get_url(path)

        if not request:
            logger.error("Request method not recognised or implemented.")

        logger.info("Sending Magento %s request on URL: %s.", method, url)
        response = request(url=url, headers=headers, data=payload)
        return self.parse_response(response)

    def get_customer_cart(self):
        success, cart_id = self.handle_request('carts/mine', self._POST_METHOD, self.get_headers(self._MAGENTO_USER_KEY))
        if success:
            return cart_id;

    def add_product_to_cart(self, product_sku, quantity=1):
        cart_id = self.get_customer_cart()
        if cart_id:
            data= {
                'cartItem': {
                    'sku': product_sku,
                    'qty': quantity,
                    'quote_id': cart_id
                }
            }
            success, data = self.handle_request('carts/mine/items', self._POST_METHOD, self.get_headers(self._MAGENTO_USER_KEY), data)
            if success:
                return
        raise InvalidMagentoResponseError("Unable to add product in Magento user cart.")

    def generate_costomer_token(self, user_email):
        data = {
            'email': user_email
        }
        success, data = self.handle_request('costomer/token/getUserToken', self._POST_METHOD, self.get_headers(self._MAGENTO_LMS_INTEGRATION_TOKEN), data)
        if success:
            self._MAGENTO_USER_KEY = data
