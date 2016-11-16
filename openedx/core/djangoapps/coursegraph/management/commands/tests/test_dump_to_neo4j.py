# coding=utf-8
"""
Tests for the dump_to_neo4j management command.
"""
from __future__ import unicode_literals

import ddt
import mock
from django.core.management import call_command

from openedx.core.djangoapps.coursegraph.tests.helpers import TestDumpToNeo4jCommandBase


@ddt.ddt
class TestDumpToNeo4jCommand(TestDumpToNeo4jCommandBase):
    """
    Tests for the dump to neo4j management command
    """

    @mock.patch('openedx.core.djangoapps.coursegraph.management.commands.dump_to_neo4j.initialize_graph')
    @ddt.data(1, 2)
    def test_dump_specific_courses(self, number_of_courses, mock_initialize_graph):
        """
        Test that you can specify which courses you want to dump.
        """
        mock_graph = mock_initialize_graph.return_value
        mock_transaction = mock.Mock()
        mock_graph.begin.return_value = mock_transaction

        call_command(
            'dump_to_neo4j',
            courses=self.course_strings[:number_of_courses],
            host='mock_host',
            http_port=7474,
            user='mock_user',
            password='mock_password',
        )

        self.assertEqual(mock_graph.begin.call_count, number_of_courses)
        self.assertEqual(mock_transaction.commit.call_count, number_of_courses)
        self.assertEqual(mock_transaction.commit.rollback.call_count, 0)

    @mock.patch('openedx.core.djangoapps.coursegraph.management.commands.dump_to_neo4j.initialize_graph')
    def test_dump_skip_course(self, mock_graph_class):
        """
        Test that you can skip courses.
        """
        mock_graph = mock_graph_class.return_value
        mock_transaction = mock.Mock()
        mock_graph.begin.return_value = mock_transaction

        call_command(
            'dump_to_neo4j',
            skip=self.course_strings[:1],
            host='mock_host',
            http_port=7474,
            user='mock_user',
            password='mock_password',
        )

        self.assertEqual(mock_graph.begin.call_count, 1)
        self.assertEqual(mock_transaction.commit.call_count, 1)
        self.assertEqual(mock_transaction.commit.rollback.call_count, 0)

    @mock.patch('openedx.core.djangoapps.coursegraph.management.commands.dump_to_neo4j.initialize_graph')
    def test_dump_skip_beats_specifying(self, mock_graph_class):
        """
        Test that if you skip and specify the same course, you'll skip it.
        """
        mock_graph = mock_graph_class.return_value
        mock_transaction = mock.Mock()
        mock_graph.begin.return_value = mock_transaction

        call_command(
            'dump_to_neo4j',
            skip=self.course_strings[:1],
            courses=self.course_strings[:1],
            host='mock_host',
            http_port=7474,
            user='mock_user',
            password='mock_password',
        )

        self.assertEqual(mock_graph.begin.call_count, 0)
        self.assertEqual(mock_transaction.commit.call_count, 0)
        self.assertEqual(mock_transaction.commit.rollback.call_count, 0)

    @mock.patch('openedx.core.djangoapps.coursegraph.management.commands.dump_to_neo4j.initialize_graph')
    def test_dump_all_courses(self, mock_graph_class):
        """
        Test if you don't specify which courses to dump, then you'll dump
        all of them.
        """
        mock_graph = mock_graph_class.return_value
        mock_transaction = mock.Mock()
        mock_graph.begin.return_value = mock_transaction

        call_command(
            'dump_to_neo4j',
            host='mock_host',
            http_port=7474,
            user='mock_user',
            password='mock_password',
        )

        self.assertEqual(mock_graph.begin.call_count, 2)
        self.assertEqual(mock_transaction.commit.call_count, 2)
        self.assertEqual(mock_transaction.commit.rollback.call_count, 0)
