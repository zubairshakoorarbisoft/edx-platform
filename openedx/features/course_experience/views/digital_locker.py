"""
Fragment for rendering the course reviews panel
"""
from django.template.loader import render_to_string
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_control
from edxmako.shortcuts import render_to_response
from web_fragments.fragment import Fragment

from lms.djangoapps.courseware.views.views import CourseTabView
from openedx.core.djangoapps.plugin_api.views import EdxFragmentView


class DigitalLockerView(CourseTabView):
    """
    The digital locker page.
    """
    @method_decorator(cache_control(no_cache=True, no_store=True, must_revalidate=True))
    def get(self, request, course_id, **kwargs):
        """
        Displays the digital locker for the specified course.
        """
        # Render the bookmarks list as a fragment
        digital_locker_fragment = DigitalLockerFragmentView().render_to_fragment(request)

        # Render the course bookmarks page
        context = {
            'digital_locker_fragment': digital_locker_fragment,
        }
        return render_to_response('courseware/digital-locker.html', context)


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
