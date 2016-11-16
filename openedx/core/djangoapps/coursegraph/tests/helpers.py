# coding=utf-8
"""
Helpers for the coursegraph test suite
"""
from django.utils import six
from xmodule.modulestore.tests.django_utils import SharedModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory


class TestDumpToNeo4jCommandBase(SharedModuleStoreTestCase):
    """
    Base class for the test suites in this file. Sets up a couple courses.
    """
    @classmethod
    def setUpClass(cls):
        super(TestDumpToNeo4jCommandBase, cls).setUpClass()
        cls.course = CourseFactory.create()
        cls.chapter = ItemFactory.create(parent=cls.course, category='chapter')
        cls.sequential = ItemFactory.create(parent=cls.chapter, category='sequential')
        cls.vertical = ItemFactory.create(parent=cls.sequential, category='vertical')
        cls.html = ItemFactory.create(parent=cls.vertical, category='html')
        cls.problem = ItemFactory.create(parent=cls.vertical, category='problem')
        cls.video = ItemFactory.create(parent=cls.vertical, category='video')
        cls.video2 = ItemFactory.create(parent=cls.vertical, category='video')

        cls.course2 = CourseFactory.create()

        cls.course_strings = [six.text_type(cls.course.id), six.text_type(cls.course2.id)]
