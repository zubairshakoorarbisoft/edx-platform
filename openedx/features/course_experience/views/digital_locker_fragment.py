"""
Fragment for rendering the course reviews fragment
"""
from django.template.loader import render_to_string
from web_fragments.fragment import Fragment
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from openedx.core.djangoapps.plugin_api.views import EdxFragmentView

class DigitalLockerFragmentView(EdxFragmentView):
    """
    A fragment to display the digital locker.
    """
    def render_to_fragment(self, request, course_id=None, **kwargs):
        """
        Fragment to render the digital locker fragment.

        """

        course_overview = CourseOverview.get_from_id(course_id)
        bucket_name = course_overview.display_name_with_default.replace(' ','').lower()

        context = {
            'course_id': course_id,
            'bucket_name': bucket_name,
        }
        html = render_to_string('course_experience/digital-locker-fragment.html', context)
        return Fragment(html)
