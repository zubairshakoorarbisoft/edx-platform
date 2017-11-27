"""
Views to show a course outline.
"""
from django.template.context_processors import csrf
from django.template.loader import render_to_string
from opaque_keys.edx.keys import CourseKey
from web_fragments.fragment import Fragment


from courseware.courses import get_course_overview_with_access
from openedx.core.djangoapps.plugin_api.views import EdxFragmentView

from ..utils import get_course_outline_block_tree
from util.milestones_helpers import get_course_content_milestones_by_course, milestones_achieved_by_user


class CourseOutlineFragmentView(EdxFragmentView):
    """
    Course outline fragment to be shown in the unified course view.
    """

    def render_to_fragment(self, request, course_id=None, page_context=None, **kwargs):
        """
        Renders the course outline as a fragment.
        """
        course_key = CourseKey.from_string(course_id)
        course_overview = get_course_overview_with_access(request.user, 'load', course_key, check_if_enrolled=True)
        course_block_tree = get_course_outline_block_tree(request, course_id)

        if not course_block_tree:
            return None

        completed_milestones = milestones_achieved_by_user(request.user, course_id)


        milestones = get_course_content_milestones_by_course(
            course_id=course_key,
            relationship='requires',
            user_id=request.user.id)

        content_block_milestones = {}
        for milestone in milestones:
            content_block_milestones[ milestone['content_id'] ] = {
                'completed_prereqs': False
            }

        context = {
            'csrf': csrf(request)['csrf_token'],
            'course': course_overview,
            'blocks': course_block_tree,
            'milestones': content_block_milestones
        }
        html = render_to_string('course_experience/course-outline-fragment.html', context)
        return Fragment(html)
