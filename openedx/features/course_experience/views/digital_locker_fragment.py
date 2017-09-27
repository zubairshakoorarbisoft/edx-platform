"""
Fragment for rendering the course reviews fragment
"""
from django.template.loader import render_to_string
from web_fragments.fragment import Fragment
from openedx.core.djangoapps.plugin_api.views import EdxFragmentView

class DigitalLockerFragmentView(EdxFragmentView):
    """
    A fragment to display the digital locker.
    """
    def render_to_fragment(self, request, course_id=None, **kwargs):
        """
        Fragment to render the digital locker fragment.

        """
        context = {}
        html = render_to_string('course_experience/digital-locker-fragment.html', context)
        return Fragment(html)
