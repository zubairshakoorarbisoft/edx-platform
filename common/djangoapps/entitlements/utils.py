from .models import CourseEntitlement
from opaque_keys.edx.keys import CourseKey


def get_json_entitlements_by_user(self, username):
    # if not ApiKeyHeaderPermission().has_permission(request, self):
    #     return Response('No Permission')
    list_entitlements = []

    for entitlement in CourseEntitlement.entitlements_for_username(username).all():
        list_entitlements.append({
            'user_id': entitlement.user_id.id,
            'course_id': entitlement.root_course_id,
            'enroll_end_date': entitlement.enroll_end_date,
            'mode': entitlement.mode,
            'is_active': entitlement.is_active
        })
    return {'entitlements': list_entitlements}


def get_list_course_entitlements(user):
    list_entitlements = []

    # TODO: Add filtering
    for entitlement in CourseEntitlement.entitlements_for_user(user).all():
        list_entitlements.append(entitlement)

    return list_entitlements


def is_user_entitled_to_course(user, course):
    is_entitled = False

    course_entitlement = CourseEntitlement.get_user_course_entitlement(user, course)
    if course_entitlement is not None and course_entitlement.is_active:
        is_entitled = True

    return is_entitled


def is_user_entitlement_enrolled(user, course_run_id):
    entitlement = CourseEntitlement.get_user_course_entitlement(user, get_course_id(course_run_id))
    if (
            entitlement is not None and
            entitlement.enrollment_course_id is not None and
            entitlement.is_active
       ):
        return True
    return False


def get_course_id(course_run_id):
    return course_run_id.org + '+' + course_run_id.course
