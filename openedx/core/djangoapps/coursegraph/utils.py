"""
Contains code for the modulestore serializer
"""
from __future__ import unicode_literals, print_function

import logging

from django.utils import six
from opaque_keys.edx.keys import CourseKey
from py2neo import Node, Relationship, authenticate, Graph
from py2neo.compat import integer, string, unicode as neo4j_unicode
from request_cache.middleware import RequestCache
from xmodule.modulestore.django import modulestore

log = logging.getLogger(__name__)

# When testing locally, neo4j's bolt logger was noisy, so we'll only have it
# emit logs if there's an error.
bolt_log = logging.getLogger('neo4j.bolt')  # pylint: disable=invalid-name
bolt_log.setLevel(logging.ERROR)

PRIMITIVE_NEO4J_TYPES = (integer, string, neo4j_unicode, float, bool)


class ModuleStoreSerializer(object):
    """
    Class with functionality to serialize a modulestore into subgraphs,
    one graph per course.
    """

    def __init__(self, courses=None, skip=None, initialize=True):
        """
        Sets the object's course_keys attribute from the `courses` parameter.
        If that parameter isn't furnished, loads all course_keys from the
        modulestore.
        Filters out course_keys in the `skip` parameter, if provided.
        :param courses: string serialization of course keys
        :param skip: string serialization of course keys
        """
        if not initialize:
            return
        if courses:
            course_keys = [CourseKey.from_string(course.strip()) for course in courses]
        else:
            course_keys = [
                course.id for course in modulestore().get_course_summaries()
            ]
        if skip is not None:
            skip_keys = [CourseKey.from_string(course.strip()) for course in skip]
            course_keys = [course_key for course_key in course_keys if course_key not in skip_keys]
        self.course_keys = course_keys

    @staticmethod
    def serialize_item(item):
        """
        Args:
            item: an XBlock

        Returns:
            fields: a dictionary of an XBlock's field names and values
            label: the name of the XBlock's type (i.e. 'course'
            or 'problem')
        """
        # convert all fields to a dict and filter out parent and children field
        fields = dict(
            (field, field_value.read_from(item))
            for (field, field_value) in six.iteritems(item.fields)
            if field not in ['parent', 'children']
        )

        course_key = item.scope_ids.usage_id.course_key

        # set or reset some defaults
        fields['edited_on'] = six.text_type(getattr(item, 'edited_on', ''))
        fields['display_name'] = item.display_name_with_default
        fields['org'] = course_key.org
        fields['course'] = course_key.course
        fields['run'] = course_key.run
        fields['course_key'] = six.text_type(course_key)
        fields['location'] = six.text_type(item.location)

        label = item.scope_ids.block_type

        # prune some fields
        if label == 'course':
            if 'checklists' in fields:
                del fields['checklists']

        return fields, label

    def serialize_course(self, course_id):
        """
        Args:
            course_id: CourseKey of the course we want to serialize

        Returns:
            nodes: a list of py2neo Node objects
            relationships: a list of py2neo Relationships objects

        Serializes a course into Nodes and Relationships
        """
        # create a location to node mapping we'll need later for
        # writing relationships
        location_to_node = {}
        items = modulestore().get_items(course_id)

        # create nodes
        nodes = []
        for item in items:
            fields, label = self.serialize_item(item)

            for field_name, value in six.iteritems(fields):
                fields[field_name] = self.coerce_types(value)

            node = Node(label, 'item', **fields)
            nodes.append(node)
            location_to_node[item.location] = node

        # create relationships
        relationships = []
        for item in items:
            for child_loc in item.get_children():
                parent_node = location_to_node.get(item.location)
                child_node = location_to_node.get(child_loc.location)
                if parent_node is not None and child_node is not None:
                    relationship = Relationship(parent_node, "PARENT_OF", child_node)
                    relationships.append(relationship)

        return nodes, relationships

    @staticmethod
    def coerce_types(value):
        """
        Args:
            value: the value of an xblock's field

        Returns: either the value, a text version of the value, or, if the
        value is a list, a list where each element is converted to text.
        """
        coerced_value = value
        if isinstance(value, list):
            coerced_value = [six.text_type(element) for element in coerced_value]

        # if it's not one of the types that neo4j accepts,
        # just convert it to text
        elif not isinstance(value, PRIMITIVE_NEO4J_TYPES):
            coerced_value = six.text_type(value)

        return coerced_value

    @staticmethod
    def add_to_transaction(neo4j_entities, transaction):
        """
        Args:
            neo4j_entities: a list of Nodes or Relationships
            transaction: a neo4j transaction
        """
        for entity in neo4j_entities:
            transaction.create(entity)

    def dump_course_to_neo4j(self, graph, course_key):
        """
        Serializes a course and then dumps it to neo4j
        Args:
            graph: py2neo Graph object
            course_key: a CourseKey object

        Returns: bool if the dump was successful
        """
        nodes, relationships = self.serialize_course(course_key)
        log.info(
            "%d nodes and %d relationships in %s",
            len(nodes),
            len(relationships),
            course_key,
        )

        transaction = graph.begin()
        course_string = six.text_type(course_key)
        try:
            # first, delete existing course
            transaction.run(
                "MATCH (n:item) WHERE n.course_key='{}' DETACH DELETE n".format(
                    course_string
                )
            )

            # now, re-add it
            self.add_to_transaction(nodes, transaction)
            self.add_to_transaction(relationships, transaction)
            transaction.commit()

        except Exception:  # pylint: disable=broad-except
            log.exception(
                "Error trying to dump course %s to neo4j, rolling back",
                course_string
            )
            transaction.rollback()
            success = False

        else:
            success = True

        return success

    def dump_courses_to_neo4j(self, graph):
        """
        Parameters
        ----------
        graph: py2neo graph object
        override_cache: serialize the courses even if they'be been recently
            serialized

        Returns two lists: one of the courses that were successfully written
          to neo4j, and one of courses that were not.
        -------
        """
        total_number_of_courses = len(self.course_keys)

        successful_courses = []
        unsuccessful_courses = []

        for index, course_key in enumerate(self.course_keys):
            # first, clear the request cache to prevent memory leaks
            RequestCache.clear_request_cache()

            log.info(
                "Now exporting %s to neo4j: course %d of %d total courses",
                course_key,
                index + 1,
                total_number_of_courses,
            )

            success = self.dump_course_to_neo4j(graph, course_key)
            if success:
                successful_courses.append(six.text_type(course_key))
            else:
                unsuccessful_courses.append(six.text_type(course_key))

        return successful_courses, unsuccessful_courses


def initialize_graph(**config):
    """

    Args:
        **config: configration parameters for setting up neo4j

    Returns: a py2neo Graph instance
    """
    authenticate(
        "{host}:{port}".format(
            host=config['host'],
            port=config.get('https_port') if config['secure'] else config.get('http_port')
        ),
        config['user'],
        config['password'],
    )
    graph = Graph(**config)

    return graph
