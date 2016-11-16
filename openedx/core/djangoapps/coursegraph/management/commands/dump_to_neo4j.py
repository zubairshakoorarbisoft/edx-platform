"""
This file contains a management command for exporting the modulestore to
neo4j, a graph database.
"""
from __future__ import unicode_literals, print_function

import logging

from django.core.management.base import BaseCommand
from django.utils import six
from py2neo import Graph, authenticate
from openedx.core.djangoapps.coursegraph.utils import ModuleStoreSerializer, \
    initialize_graph

log = logging.getLogger(__name__)

# When testing locally, neo4j's bolt logger was noisy, so we'll only have it
# emit logs if there's an error.
bolt_log = logging.getLogger('neo4j.bolt')  # pylint: disable=invalid-name
bolt_log.setLevel(logging.ERROR)

class Command(BaseCommand):
    """
    Command to dump modulestore data to neo4j

    Takes the following named arguments:
      host: the host of the neo4j server
      https_port: the port on the neo4j server that accepts https requests
      http_port: the port on the neo4j server that accepts http requests
      secure: if set, connects to server over https, otherwise uses http
      user: the username for the neo4j user
      password: the user's password
      courses: list of course key strings to serialize. If not specified, all
        courses in the modulestore are serialized.
      skip: list of course key strings of courses to skip. If not specified,
        no courses are skipped

    Example usage:
      python manage.py lms dump_to_neo4j --host localhost --https_port 7473 \
        --secure --user user --password password --settings=aws
    """
    def add_arguments(self, parser):
        parser.add_argument('--host', type=six.text_type)
        parser.add_argument('--https_port', type=int, default=7473)
        parser.add_argument('--http_port', type=int, default=7474)
        parser.add_argument('--secure', action='store_true')
        parser.add_argument('--user', type=six.text_type)
        parser.add_argument('--password', type=six.text_type)
        parser.add_argument('--courses', type=six.text_type, nargs='*')
        parser.add_argument('--skip', type=six.text_type, nargs='*')

    def handle(self, *args, **options):  # pylint: disable=unused-argument
        """
        Iterates through each course, serializes them into graphs, and saves
        those graphs to neo4j.
        """
        host = options['host']
        https_port = options['https_port']
        http_port = options['http_port']
        secure = options['secure']
        neo4j_user = options['user']
        neo4j_password = options['password']

        graph = initialize_graph(
            bolt=True,
            password=neo4j_password,
            user=neo4j_user,
            https_port=https_port,
            http_port=http_port,
            host=host,
            secure=secure,
        )

        mss = ModuleStoreSerializer(options['courses'], options['skip'])

        successful_courses, unsuccessful_courses = mss.dump_courses_to_neo4j(
            graph
        )

        if not successful_courses and not unsuccessful_courses:
            print("No courses exported to neo4j at all!")
            return

        if successful_courses:
            print(
                "These courses exported to neo4j successfully:\n\t" +
                "\n\t".join(successful_courses)
            )
        else:
            print("No courses exported to neo4j successfully.")

        if unsuccessful_courses:
            print(
                "These courses did not export to neo4j successfully:\n\t" +
                "\n\t".join(unsuccessful_courses)
            )
        else:
            print("All courses exported to neo4j successfully.")
