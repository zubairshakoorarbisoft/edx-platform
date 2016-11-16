# coding=utf-8
"""
Tests for coursegraph utilities
"""
from __future__ import unicode_literals

import ddt
import mock

from openedx.core.djangoapps.coursegraph.tests.helpers import TestDumpToNeo4jCommandBase
from openedx.core.djangoapps.coursegraph.utils import ModuleStoreSerializer

@ddt.ddt
class TestModuleStoreSerializer(TestDumpToNeo4jCommandBase):
    """
    Tests for the ModuleStoreSerializer
    """
    @classmethod
    def setUpClass(cls):
        """Any ModuleStore course/content operations can go here."""
        super(TestModuleStoreSerializer, cls).setUpClass()
        cls.mss = ModuleStoreSerializer()

    def test_serialize_item(self):
        """
        Tests the serialize_item method.
        """
        fields, label = self.mss.serialize_item(self.course)
        self.assertEqual(label, "course")
        self.assertIn("edited_on", fields.keys())
        self.assertIn("display_name", fields.keys())
        self.assertIn("org", fields.keys())
        self.assertIn("course", fields.keys())
        self.assertIn("run", fields.keys())
        self.assertIn("course_key", fields.keys())
        self.assertIn("location", fields.keys())
        self.assertNotIn("checklist", fields.keys())

    def test_serialize_course(self):
        """
        Tests the serialize_course method.
        """
        nodes, relationships = self.mss.serialize_course(
            self.course.id
        )
        self.assertEqual(len(nodes), 9)
        self.assertEqual(len(relationships), 7)

    @ddt.data(
        (1, 1),
        (object, "<type 'object'>"),
        (1.5, 1.5),
        ("úñîçø∂é", "úñîçø∂é"),
        (b"plain string", b"plain string"),
        (True, True),
        (None, "None"),
        ((1,), "(1,)"),
        # list of elements should be coerced into a list of the
        # string representations of those elements
        ([object, object], ["<type 'object'>", "<type 'object'>"])
    )
    @ddt.unpack
    def test_coerce_types(self, original_value, coerced_expected):
        """
        Tests the coerce_types helper
        """
        coerced_value = self.mss.coerce_types(original_value)
        self.assertEqual(coerced_value, coerced_expected)

    def test_dump_single_course_to_neo4j(self):
        """
        Tests the dump_course_to_neo4j method works against a mock
        py2neo Graph
        """
        mock_graph = mock.Mock()
        mock_transaction = mock.Mock()
        mock_graph.begin.return_value = mock_transaction

        success = self.mss.dump_course_to_neo4j(mock_graph, self.course.id)

        self.assertEqual(mock_graph.begin.call_count, 1)
        self.assertEqual(mock_transaction.commit.call_count, 1)
        self.assertEqual(mock_transaction.rollback.call_count, 0)

        self.assertEqual(mock_transaction.create.call_count, 16)
        self.assertEqual(mock_transaction.run.call_count, 1)

        self.assertTrue(success)

    def test_dump_courses_to_neo4j(self):
        """
        Tests the dump_courses_to_neo4j method works against a mock
        py2neo Graph
        """
        mock_graph = mock.Mock()
        mock_transaction = mock.Mock()
        mock_graph.begin.return_value = mock_transaction

        successful, unsuccessful = self.mss.dump_courses_to_neo4j(mock_graph)

        self.assertEqual(mock_graph.begin.call_count, 2)
        self.assertEqual(mock_transaction.commit.call_count, 2)
        self.assertEqual(mock_transaction.rollback.call_count, 0)

        # 7 nodes + 9 relationships from the first course
        # 2 nodes and no relationships from the second
        self.assertEqual(mock_transaction.create.call_count, 18)
        self.assertEqual(mock_transaction.run.call_count, 2)

        self.assertEqual(len(unsuccessful), 0)
        self.assertItemsEqual(successful, self.course_strings)

    def test_dump_to_neo4j_rollback(self):
        """
        Tests that the the dump_to_neo4j method handles the case where there's
        an exception trying to write to the neo4j database.
        """
        mock_graph = mock.Mock()
        mock_transaction = mock.Mock()
        mock_graph.begin.return_value = mock_transaction
        mock_transaction.run.side_effect = ValueError('Something went wrong!')

        successful, unsuccessful = self.mss.dump_courses_to_neo4j(mock_graph)

        self.assertEqual(mock_graph.begin.call_count, 2)
        self.assertEqual(mock_transaction.commit.call_count, 0)
        self.assertEqual(mock_transaction.rollback.call_count, 2)

        self.assertEqual(len(successful), 0)
        self.assertItemsEqual(unsuccessful, self.course_strings)
