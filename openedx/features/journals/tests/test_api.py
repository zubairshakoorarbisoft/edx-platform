from django.test import TestCase
from openedx.features.journals.api import get_cache_key


class TestJournalApi(TestCase):

    def setUp(self):
        super(TestJournalApi, self).setUp()

    def test_get_cache_key(self):
        key = get_cache_key(site_domain="example.com", resource="enterprise-learner")
        expected_key = '6f49d2662d301eeac45149648857'
        self.assertTrue(key, expected_key)
