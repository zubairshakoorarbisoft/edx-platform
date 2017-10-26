"""
Test signal handlers.
"""

from datetime import datetime

import ddt
from django.test import TestCase
from mock import patch
from opaque_keys.edx.keys import CourseKey
from pytz import utc
import six
from xblock.core import XBlock

from lms.djangoapps.grades.signals.signals import PROBLEM_WEIGHTED_SCORE_CHANGED
from student.tests.factories import UserFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory

from .. import handlers
from ..models import BlockCompletion
from .. import waffle


class CompletionWaffleMixin(object):
    """
    Quick management of the completion waffle switch for tests.
    """
    def override_waffle_switch(self, override):
        """
        Override the setting of the ENABLE_COMPLETION_TRACKING waffle switch
        for the course of the test.

        Parameters:
            override (bool): True if tracking should be enabled.
        """
        _waffle_overrider = waffle.waffle().override(waffle.ENABLE_COMPLETION_TRACKING, override)
        _waffle_overrider.__enter__()
        self.addCleanup(_waffle_overrider.__exit__, None, None, None)


class CustomScorableBlock(XBlock):
    """
    A scorable block with a custom completion strategy.
    """
    has_score = True
    has_custom_completion = True
    completion_method = 'scorable'


class ExcludedScorableBlock(XBlock):
    """
    A scorable block that is excluded from completion tracking.
    """
    has_score = True
    has_custom_completion = False
    completion_method = 'excluded'


@ddt.ddt
class ScorableCompletionHandlerTestCase(CompletionWaffleMixin, ModuleStoreTestCase):
    """
    Test the signal handler
    """

    def setUp(self):
        super(ScorableCompletionHandlerTestCase, self).setUp()
        self.course = CourseFactory.create()
        self.scorable_block = ItemFactory.create(parent=self.course, category='problem')
        self.user = UserFactory.create()
        self.override_waffle_switch(True)

    def call_handler_for_block(self, block, score_deleted=None):
        """
        Call the signal handler for the specified block.

        Optionally takes a value to pass as score_deleted.
        """
        if score_deleted is None:
            params = {}
        else:
            params = {'score_deleted': score_deleted}
        handlers.scorable_block_completion(
            sender=self,
            user_id=self.user.id,
            course_id=six.text_type(self.course.id),
            usage_id=six.text_type(block.location),
            weighted_earned=0.0,
            weighted_possible=3.0,
            modified=datetime.utcnow().replace(tzinfo=utc),
            score_db_table='submissions',
            **params
        )

    @ddt.data(
        (True, 0.0),
        (False, 1.0),
        (None, 1.0),
    )
    @ddt.unpack
    def test_handler_submits_completion(self, score_deleted, expected_completion):
        self.call_handler_for_block(self.scorable_block, score_deleted)
        completion = BlockCompletion.objects.get(
            user=self.user,
            course_key=self.course.id,
            block_key=self.scorable_block.location
        )
        self.assertEqual(completion.completion, expected_completion)

    @XBlock.register_temp_plugin(CustomScorableBlock, 'custom_scorable')
    def test_handler_skips_custom_block(self):
        custom_block = ItemFactory.create(parent=self.course, category='custom_scorable')
        self.call_handler_for_block(custom_block)
        completion = BlockCompletion.objects.filter(
            user=self.user,
            course_key=self.course.id,
            block_key=custom_block.location,
        )
        self.assertFalse(completion.exists())

    @XBlock.register_temp_plugin(ExcludedScorableBlock, 'excluded_scorable')
    def test_handler_skips_excluded_block(self):
        excluded_block = ItemFactory.create(parent=self.course, category='excluded_scorable')
        self.call_handler_for_block(excluded_block)
        completion = BlockCompletion.objects.filter(
            user=self.user,
            course_key=self.course.id,
            block_key=excluded_block.location
        )
        self.assertFalse(completion.exists())

    def test_signal_calls_handler(self):
        user = UserFactory.create()

        with patch('lms.djangoapps.completion.handlers.scorable_block_completion') as mock_handler:
            PROBLEM_WEIGHTED_SCORE_CHANGED.send_robust(
                sender=self,
                user_id=user.id,
                course_id=six.text_type(self.course.id),
                usage_id=six.text_type(self.scorable_block.location),
                weighted_earned=0.0,
                weighted_possible=3.0,
                modified=datetime.utcnow().replace(tzinfo=utc),
                score_db_table='submissions',
            )
        mock_handler.assert_called()


class DisabledCompletionHandlerTestCase(CompletionWaffleMixin, TestCase):
    """
    Test that disabling the ENABLE_COMPLETION_TRACKING waffle switch prevents
    the signal handler from submitting a completion.
    """
    def setUp(self):
        super(DisabledCompletionHandlerTestCase, self).setUp()
        self.user = UserFactory.create()
        self.course_key = CourseKey.from_string("course-v1:a+valid+course")
        self.block_key = self.course_key.make_usage_key(block_type="video", block_id="mah-video")
        self.override_waffle_switch(False)

    def test_disabled_handler_does_not_submit_completion(self):
        handlers.scorable_block_completion(
            sender=self,
            user_id=self.user.id,
            course_id=six.text_type(self.course_key),
            usage_id=six.text_type(self.block_key),
            weighted_earned=0.0,
            weighted_possible=3.0,
            modified=datetime.utcnow().replace(tzinfo=utc),
            score_db_table='submissions',
        )
        with self.assertRaises(BlockCompletion.DoesNotExist):
            BlockCompletion.objects.get(
                user=self.user,
                course_key=self.course_key,
                block_key=self.block_key
            )
