"""
Test cases for forum v2 based tasks.py 
"""
from unittest import mock
from unittest.mock import Mock

import ddt
import httpretty
from django.conf import settings
from edx_toggles.toggles.testutils import override_waffle_flag
from openedx_events.learning.signals import USER_NOTIFICATION_REQUESTED

from common.djangoapps.student.models import CourseEnrollment
from common.djangoapps.student.tests.factories import UserFactory
from lms.djangoapps.discussion.rest_api.tasks import send_response_notifications
from lms.djangoapps.discussion.rest_api.tests.utils import ThreadMock, ForumMockUtilsMixin
from openedx.core.djangoapps.notifications.config.waffle import ENABLE_NOTIFICATIONS
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory

from ..discussions_notifications import DiscussionNotificationSender
from .test_views_v2 import DiscussionAPIViewTestMixin


def _get_mfe_url(course_id, post_id):
    """
    get discussions mfe url to specific post.
    """
    return f"{settings.DISCUSSIONS_MICROFRONTEND_URL}/{str(course_id)}/posts/{post_id}"


@ddt.ddt
@override_waffle_flag(ENABLE_NOTIFICATIONS, active=True)
class TestSendResponseNotifications(DiscussionAPIViewTestMixin, ModuleStoreTestCase):
    """
    Test for the send_response_notifications function
    """

    def setUp(self):
        super().setUp()
        httpretty.reset()
        httpretty.enable()
        patcher = mock.patch(
            'openedx.core.djangoapps.discussions.config.waffle.ENABLE_FORUM_V2.is_enabled',
            return_value=False
        )
        patcher.start()
        self.addCleanup(patcher.stop)

        self.course = CourseFactory.create()
        patcher = mock.patch(
            "openedx.core.djangoapps.django_comment_common.comment_client.thread.forum_api.get_course_id_by_thread",
            return_value=self.course.id
        )
        self.mock_get_course_id_by_thread = patcher.start()
        self.addCleanup(patcher.stop)
        patcher = mock.patch(
            "openedx.core.djangoapps.django_comment_common.comment_client.models.forum_api.get_course_id_by_comment",
            return_value=self.course.id
        )
        self.mock_get_course_id_by_comment = patcher.start()
        self.addCleanup(patcher.stop)
        self.user_1 = UserFactory.create()
        CourseEnrollment.enroll(self.user_1, self.course.id)
        self.user_2 = UserFactory.create()
        CourseEnrollment.enroll(self.user_2, self.course.id)
        self.user_3 = UserFactory.create()
        CourseEnrollment.enroll(self.user_3, self.course.id)
        self.thread = ThreadMock(thread_id=1, creator=self.user_1, title='test thread')
        self.thread_2 = ThreadMock(thread_id=2, creator=self.user_2, title='test thread 2')
        self.thread_3 = ThreadMock(thread_id=2, creator=self.user_1, title='test thread 3')
        for thread in [self.thread, self.thread_2, self.thread_3]:
            self.register_get_thread_response({
                'id': thread.id,
                'course_id': str(self.course.id),
                'topic_id': 'abc',
                "user_id": thread.user_id,
                "username": thread.username,
                "thread_type": 'discussion',
                "title": thread.title,
                "commentable_id": thread.commentable_id,

            })
        self._register_subscriptions_endpoint()

        self.comment = ThreadMock(thread_id=4, creator=self.user_2, title='test comment', body='comment body')
        self.register_get_comment_response(
            {
                'id': self.comment.id,
                'thread_id': self.thread.id,
                'parent_id': None,
                'user_id': self.comment.user_id,
                'body': self.comment.body,
            }
        )

    def _register_subscriptions_endpoint(self):
        """
        Registers the endpoint for the subscriptions API
        """
        mock_response = {
            'collection': [
                {
                    '_id': 1,
                    'subscriber_id': str(self.user_2.id),
                    "source_id": self.thread.id,
                    "source_type": "thread",
                },
                {
                    '_id': 2,
                    'subscriber_id': str(self.user_3.id),
                    "source_id": self.thread.id,
                    "source_type": "thread",
                },
            ],
            'page': 1,
            'num_pages': 1,
            'subscriptions_count': 2,
            'corrected_text': None

        }
        self.register_get_subscriptions(self.thread.id, mock_response)

    def test_send_notification_to_thread_creator(self):
        """
        Test that the notification is sent to the thread creator
        """
        handler = mock.Mock()
        USER_NOTIFICATION_REQUESTED.connect(handler)

        # Post the form or do what it takes to send the signal
        send_response_notifications(
            self.thread.id,
            str(self.course.id),
            self.user_2.id,
            self.comment.id,
            parent_id=None
        )
        self.assertEqual(handler.call_count, 2)
        args = handler.call_args_list[0][1]['notification_data']
        self.assertEqual([int(user_id) for user_id in args.user_ids], [self.user_1.id])
        self.assertEqual(args.notification_type, 'new_response')
        expected_context = {
            'replier_name': self.user_2.username,
            'post_title': 'test thread',
            'email_content': self.comment.body,
            'course_name': self.course.display_name,
            'sender_id': self.user_2.id,
            'response_id': 4,
            'topic_id': None,
            'thread_id': 1,
            'comment_id': None,
        }
        self.assertDictEqual(args.context, expected_context)
        self.assertEqual(
            args.content_url,
            _get_mfe_url(self.course.id, self.thread.id)
        )
        self.assertEqual(args.app_name, 'discussion')

    def test_no_signal_on_creators_own_thread(self):
        """
        Makes sure that 1 signal is emitted if user creates response on
        their own thread.
        """
        handler = mock.Mock()
        USER_NOTIFICATION_REQUESTED.connect(handler)

        send_response_notifications(
            self.thread.id,
            str(self.course.id),
            self.user_1.id,
            self.comment.id, parent_id=None
        )
        self.assertEqual(handler.call_count, 1)

    @ddt.data(
        (None, 'response_on_followed_post'), (1, 'comment_on_followed_post')
    )
    @ddt.unpack
    def test_send_notification_to_followers(self, parent_id, notification_type):
        """
        Test that the notification is sent to the followers of the thread
        """
        self.register_get_comment_response({
            'id': self.thread.id,
            'thread_id': self.thread.id,
            'user_id': self.thread.user_id
        })
        handler = Mock()
        USER_NOTIFICATION_REQUESTED.connect(handler)

        # Post the form or do what it takes to send the signal
        notification_sender = DiscussionNotificationSender(
            self.thread,
            self.course,
            self.user_2,
            parent_id=parent_id,
            comment_id=self.comment.id
        )
        notification_sender.send_response_on_followed_post_notification()
        self.assertEqual(handler.call_count, 1)
        args = handler.call_args[1]['notification_data']
        # only sent to user_3 because user_2 is the one who created the response
        self.assertEqual([self.user_3.id], args.user_ids)
        self.assertEqual(args.notification_type, notification_type)
        expected_context = {
            'replier_name': self.user_2.username,
            'post_title': 'test thread',
            'email_content': self.comment.body,
            'course_name': self.course.display_name,
            'sender_id': self.user_2.id,
            'response_id': 4 if notification_type == 'response_on_followed_post' else parent_id,
            'topic_id': None,
            'thread_id': 1,
            'comment_id': 4 if not notification_type == 'response_on_followed_post' else None,
        }
        if parent_id:
            expected_context['author_name'] = 'dummy\'s'
            expected_context['author_pronoun'] = 'dummy\'s'
        self.assertDictEqual(args.context, expected_context)
        self.assertEqual(
            args.content_url,
            _get_mfe_url(self.course.id, self.thread.id)
        )
        self.assertEqual(args.app_name, 'discussion')
    
    def test_comment_creators_own_response(self):
        """
        Check incase post author and response auther is same only send
        new comment signal , with your as author_name.
        """
        handler = mock.Mock()
        USER_NOTIFICATION_REQUESTED.connect(handler)

        self.register_get_comment_response({
            'id': self.thread_3.id,
            'thread_id': self.thread.id,
            'user_id': self.thread_3.user_id
        })

        send_response_notifications(
            self.thread.id,
            str(self.course.id),
            self.user_3.id,
            parent_id=self.thread_2.id,
            comment_id=self.comment.id
        )
        # check if 1 call is made to the handler i.e. for the thread creator
        self.assertEqual(handler.call_count, 2)

        # check if the notification is sent to the thread creator
        args_comment = handler.call_args_list[0][1]['notification_data']
        self.assertEqual(args_comment.user_ids, [self.user_1.id])
        self.assertEqual(args_comment.notification_type, 'new_comment')
        expected_context = {
            'replier_name': self.user_3.username,
            'post_title': self.thread.title,
            'author_name': 'dummy\'s',
            'author_pronoun': 'your',
            'course_name': self.course.display_name,
            'sender_id': self.user_3.id,
            'email_content': self.comment.body,
            'response_id': 2,
            'topic_id': None,
            'thread_id': 1,
            'comment_id': 4,
        }
        self.assertDictEqual(args_comment.context, expected_context)
        self.assertEqual(
            args_comment.content_url,
            _get_mfe_url(self.course.id, self.thread.id)
        )
        self.assertEqual(args_comment.app_name, 'discussion')
