"""
Fragment for rendering the course dates sidebar.
"""


from django.http import Http404
from django.template.loader import render_to_string
from django.utils.translation import get_language_bidi
from opaque_keys.edx.keys import CourseKey
from web_fragments.fragment import Fragment

from lms.djangoapps.courseware.courses import get_course_date_blocks, get_course_with_access
from openedx.core.djangoapps.plugin_api.views import EdxFragmentView
from openedx.features.clearesult_features.credits.utils import get_course_credits_list

class CourseCreditsFragmentView(EdxFragmentView):
    """
    A fragment to show credits offered by the course.
    """
    template_name = 'course_experience/course-credits-fragment.html'

    def render_to_fragment(self, request, course_id=None, **kwargs):
        """
        Render the course credits fragment.
        """
        course_key = CourseKey.from_string(course_id)
        context = {
            'course_credits': get_course_credits_list(course_key)
        }
        html = render_to_string(self.template_name, context)
        credits_fragment = Fragment(html)
        self.add_fragment_resource_urls(credits_fragment)

        return credits_fragment
