"""
Fragment for rendering the course reviews panel
"""
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_control
from edxmako.shortcuts import render_to_response

from lms.djangoapps.courseware.views.views import CourseTabView
from .digital_locker_fragment import DigitalLockerFragmentView

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
        digital_locker_fragment = DigitalLockerFragmentView().render_to_fragment(request, course_id=course_id)

        # Render the course bookmarks page
        context = {
            'digital_locker_fragment': digital_locker_fragment,
        }
        return render_to_response('courseware/digital-locker.html', context)
