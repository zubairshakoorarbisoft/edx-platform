from django.conf import settings
from django.shortcuts import get_object_or_404

from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers
from edxmako.shortcuts import render_to_response
from courseware.access import has_access
from courseware.courses import sort_by_announcement, sort_by_start_date

from .models import Category


def course_category_list(request):
    # categories = Category.get_category_tree(enabled=True)
    categories = Category.objects.filter(enabled=True)
    return render_to_response('category_list.html', {'categories': categories})


def course_category(request, slug):
    category = get_object_or_404(Category, slug=slug, enabled=True)
    courses = []
    permission_name = configuration_helpers.get_value(
        'COURSE_CATALOG_VISIBILITY_PERMISSION',
        settings.COURSE_CATALOG_VISIBILITY_PERMISSION
    )
    descendants = category.get_descendants(include_self=False).filter(parent=category)
    # category.get_ancestors()
    for course_id in category.get_course_ids():
        try:
            course = CourseOverview.get_from_id(course_id)
            if has_access(request.user, permission_name, course):
                courses.append(course)
        except:
            continue

    if configuration_helpers.get_value(
        "ENABLE_COURSE_SORTING_BY_START_DATE",
        settings.FEATURES["ENABLE_COURSE_SORTING_BY_START_DATE"]
    ):
        courses = sort_by_start_date(courses)
    else:
        courses = sort_by_announcement(courses)

    return render_to_response('category.html', {
        'courses': courses,
        'category': category,
        'descendants': descendants,
        # 'uses_bootstrap': True,
    })

