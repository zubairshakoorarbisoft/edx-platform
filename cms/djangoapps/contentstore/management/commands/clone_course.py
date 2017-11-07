"""
Script for cloning a course
"""
from __future__ import print_function

from django.core.management.base import BaseCommand
from opaque_keys.edx.keys import CourseKey

from student.roles import CourseInstructorRole, CourseStaffRole
from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.django import modulestore
from django.contrib.auth.models import User
from xmodule.modulestore.xml_importer import import_library_from_xml
from xmodule.contentstore.django import contentstore
from contentstore.utils import add_instructor, reverse_library_url
#
# To run from command line: ./manage.py cms clone_course --settings=dev master/300/cough edx/111/foo
#
class Command(BaseCommand):
    """
    Create 600 libraries
    """
    help = 'Clone a MongoDB backed course to another location'

    def handle(self, *args, **options):
        """
        Execute the command
        """

        dirpath = u'library'
        LIBRARY_ROOT = 'library.xml'
        root_name = LIBRARY_ROOT
        import_func = import_library_from_xml

        user = User.objects.get(username='honor')
        store = modulestore()


        for i in range(1,600):
            with store.default_store(ModuleStoreEnum.Type.split):
                new_lib = store.create_library(
                    org='Arbisoft',
                    library='library{}'.format(i),
                    user_id=user.id,
                    fields={"display_name": 'New Library'},
                )
            # Give the user admin ("Instructor") role for this library:
            add_instructor(new_lib.location.library_key, user, user)

            courselike_module = modulestore().get_library(new_lib.location.library_key)

            courselike_items = import_func(
                modulestore(), user.id,
                u'/edx/app/edxapp/edx-platform', [dirpath],
                load_error_modules=False,
                static_content_store=contentstore(),
                target_id=new_lib.location.library_key
            )
