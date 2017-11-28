"""
Views to show a course outline.
"""
from django.template.context_processors import csrf
from django.template.loader import render_to_string
from opaque_keys.edx.keys import CourseKey
from web_fragments.fragment import Fragment

from lms.djangoapps.course_api.blocks.api import get_blocks
from courseware.courses import get_course_overview_with_access
from openedx.core.djangoapps.plugin_api.views import EdxFragmentView

from ..utils import get_course_outline_block_tree, get_all_course_blocks
from util.milestones_helpers import get_all_course_content_milestones, get_course_content_milestones_by_course, milestones_achieved_by_user, get_course_content_milestones


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
        all_course_blocks = get_all_course_blocks(request, course_id)

        if not course_block_tree:
            return None


        content_milestones = {}
        
        #TODO: should i be using a user id here? probably
        course_prereqs = get_all_course_content_milestones(course_key) #, relationship='requires')

        unfulfilled_prereqs = get_course_content_milestones_by_course(
            course_id=course_key,
            relationship='requires',
            user_id=request.user.id)

        for milestone in course_prereqs:
            # check that its a 'requires' relationship
            # TODO: just grab the 'requires' milestones from the database
            if milestone['requirements']: 
                content_milestones[ milestone['content_id'] ] = {
                    'completed_prereqs': True,
                    'min_score': milestone['requirements']['min_score']
                }
        
        for milestone in unfulfilled_prereqs:
            content_milestones[milestone['content_id']]['completed_prereqs'] = False
            content_milestones[milestone['content_id']]['prereq'] = all_course_blocks['blocks'][milestone['namespace'].replace('.gating','')]['display_name']
            #TODO: can there be multiple prereqs?

        context = {
            'csrf': csrf(request)['csrf_token'],
            'course': course_overview,
            'blocks': course_block_tree,
            'milestones': content_milestones
        }
        html = render_to_string('course_experience/course-outline-fragment.html', context)
        return Fragment(html)
