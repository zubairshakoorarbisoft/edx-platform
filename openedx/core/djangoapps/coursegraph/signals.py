"""
Signal handlers for the CourseGraph application
"""
import logging

from celery.task import task
from django.dispatch.dispatcher import receiver
from xmodule.modulestore.django import SignalHandler

from openedx.core.djangoapps.coursegraph.utils import initialize_graph, ModuleStoreSerializer

log = logging.getLogger(__name__)


@receiver(SignalHandler.course_published)
def _listen_for_course_publish(sender, course_key, **kwargs):  # pylint: disable=unused-argument
    """
    When a course is published, update neo4j accordingly.
    """
    dump_course_to_neo4j.apply_async([course_key])

@task()
def dump_course_to_neo4j(course_key):
    mss = ModuleStoreSerializer(initialize=False)
    graph = initialize_graph(
        bolt=True,
        password='password',
        user='neo4j',
        https_port=7473,
        http_port=7474,
        host='localhost',
        secure=True,
    )
    mss.dump_course_to_neo4j(graph, course_key)
