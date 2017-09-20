from .models import CourseEntitlement


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
