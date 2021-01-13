"""
Views for Clearesult V0 APIs
"""
import json

from django.contrib.sites.models import Site
from django.db import IntegrityError
from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import generics
from rest_framework import permissions
from rest_framework import viewsets
from rest_framework import status
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework.exceptions import NotFound
from rest_framework.response import Response

from edx_rest_framework_extensions.auth.jwt.authentication import JwtAuthentication

from openedx.core.lib.api.authentication import BearerAuthentication
from openedx.features.clearesult_features.utils import get_site_users
from openedx.features.clearesult_features.models import (
    ClearesultCreditProvider, UserCreditsProfile, ClearesultCatalog,
    ClearesultCourse, ClearesultLocalAdmin, ClearesultGroupLinkage,
    ClearesultGroupLinkedCatalogs
)
from openedx.features.clearesult_features.api.v0.serializers import (
    UserCreditsProfileSerializer, ClearesultCreditProviderSerializer,
    ClearesultCatalogSerializer, ClearesultCourseSerializer,
    UserSerializer, SiteSerializer, ClearesultGroupsSerializer,
    ClearesultMandatoryCoursesSerializer
)
from openedx.features.clearesult_features.api.v0.validators import (
    validate_data_for_catalog_creation, validate_data_for_catalog_updation, validate_clearesult_catalog_pk,
    validate_sites_for_local_admin, validate_catalog_update_deletion
)
from openedx.features.clearesult_features.utils import is_local_admin_or_superuser

class IsSelf(permissions.BasePermission):

    message = 'You are not authorized to edit this profile.'

    def has_permission(self, request, view):
        """
        User only has permission to perform the action if they are changing
        their own objects.
        """
        user_credit_profile_id = view.kwargs['pk']
        current_user = request.user

        profile = None
        try:
            profile = UserCreditsProfile.objects.get(pk=user_credit_profile_id)
        except UserCreditsProfile.DoesNotExist:
            return False
        return profile.user == current_user


class IsAdminOrLocalAdmin(permissions.BasePermission):

    message = 'You are not authorized to perform this action.'

    def has_permission(self, request, view):
        return is_local_admin_or_superuser(request.user)


class UserCreditProfileViewset(viewsets.ModelViewSet):
    authentication_classes = (SessionAuthentication, JwtAuthentication, )
    serializer_class = UserCreditsProfileSerializer
    pagination_class = None

    def get_permissions(self):
        permission_classes = []

        if self.action in ['create', 'list']:
            permission_classes = [permissions.IsAuthenticated]

        elif self.action in ['partial_update', 'destroy']:
            permission_classes = [permissions.IsAuthenticated, IsSelf]

        return [permission() for permission in permission_classes]

    def get_queryset(self):
        user = self.request.user
        return user.user_credit_profile.all()

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class ClearesultCreditProviderListView(generics.ListAPIView):
    """
    Return a list of credit providers in the following form:

    Get /clearesult/api/v0/credit_providers/
    ```
    [
        {
            "short_code": "one",
            "name": "One",
            "id": 1
        },
        {
            "short_code": "two",
            "name": "Two",
            "id": 2
        }
    ]
    ```
    """
    queryset = ClearesultCreditProvider.objects.all()
    authentication_classes = (JwtAuthentication, SessionAuthentication,)
    permission_classes = (permissions.IsAuthenticated, )
    serializer_class = ClearesultCreditProviderSerializer
    pagination_class = None


class ClearesultCatalogViewset(viewsets.ViewSet):
    authentication_classes = [BasicAuthentication, SessionAuthentication, BearerAuthentication, JwtAuthentication]
    permission_classes = [permissions.IsAuthenticated, IsAdminOrLocalAdmin]

    def list(self, request):
        """
        Return the list of Clearesult Catalogs in the following form
        GET /clearesult/api/v0/catalogs/

        [
            {
                "id": 39
                "name": "Dummy catalog"
                "site": {
                    "id": 1,
                    "domain": "localhost:18000"
                },
                "clearesult_courses": [
                    {
                        "course_name": "Testing automata course",
                        "course_id": "course-v1:edx+22+2020_T122",
                        "site": {
                            "id": 1,
                            "domain": "localhost:18000"
                        }
                    },
                    ...
                    ...
                ]
            },
            ...
            ...
        ]

        "site": null means that course or catalog is public
        """
        queryset = ClearesultCatalog.objects.select_related('site').prefetch_related('clearesult_courses')
        if not request.user.is_superuser:
            error, allowed_sites = validate_sites_for_local_admin(request.user)
            if error:
                return error
            queryset = queryset.filter(Q(site__in=allowed_sites) | Q(site=None))

        serializer = ClearesultCatalogSerializer(queryset, many=True)
        return Response(serializer.data)

    def create(self, request):
        """
        Create a new catalog and accept data in the following format
        POST /clearesult/api/v0/catalogs/

        {
            "name": "Dummy catalog name",
            "site": {
                "domain": "localhost:18000"
            },
            "clearesult_courses": [
                "course-v1:edx+22+2020_T122",
                "course-v1:edx+22+2020_T123",
                "course-v1:edx+22+2020_T124"
            ]
        }


        "site": {} means that catalog will be public
        """
        error, allowed_sites = validate_sites_for_local_admin(request.user)
        if error:
            return error

        data = request.data
        error, validated_data = validate_data_for_catalog_creation(data, request.user, allowed_sites)
        if error:
            return error

        name = validated_data.get('name')
        site = validated_data.get('site')
        courses = validated_data.get('clearesult_courses')

        if not request.user.is_superuser:
            try:
                ClearesultLocalAdmin.objects.get(user=request.user, site=site)
            except ClearesultLocalAdmin.DoesNotExist:
                return Response(
                    {'detail': 'You are not allowed to perform this action'},
                    status=status.HTTP_403_FORBIDDEN
                )

        try:
            instance = ClearesultCatalog.objects.create(name=name, site=site)
        except IntegrityError:
            return Response(
                {'detail': 'A clearesult catalog with this name and site already exists.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if len(courses) > 0:
            instance.clearesult_courses.add(*courses)

        serializer = ClearesultCatalogSerializer(instance)
        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        """
        Return a single instance of catalog as per pk
        GET /clearesult/api/v0/catalogs/1
        """
        queryset = ClearesultCatalog.objects.select_related('site').prefetch_related('clearesult_courses')
        if not request.user.is_superuser:
            error, allowed_sites = validate_sites_for_local_admin(request.user)
            if error:
                return error
            queryset = queryset.filter(Q(site__in=allowed_sites) | Q(site=None))

        data = get_object_or_404(queryset, pk=pk)
        serializer = ClearesultCatalogSerializer(data)
        return Response(serializer.data)

    def partial_update(self, request, pk=None):
        """
        Partially update the requested catalog
        PATCH /clearesult/api/v0/catalogs/1

        {
            "name": "Dummy new name",
            "clearesult_courses": [
                "course-v1:edx+22+2020_T122",
                "course-v1:edx+22+2020_T123"
            ]
        }

        not receiving site as site can not be changed.
        """
        error, allowed_sites = validate_sites_for_local_admin(request.user)
        if error:
            return error

        data = request.data
        data['pk'] = pk
        error, validated_data = validate_data_for_catalog_updation(data, request.user, allowed_sites)
        if error:
            return error

        name = validated_data.get('name')
        courses = validated_data.get('clearesult_courses')
        instance = validated_data.get('clearesult_catalog')

        if not request.user.is_superuser:
            error = validate_catalog_update_deletion(request.user, instance)
            if error:
                return error

        try:
            instance.name = name
            instance.save()
        except IntegrityError:
            return Response(
                {'detail': 'A clearesult catalog with this name and site already exists.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # updating site is not allowed
        instance.clearesult_courses.clear()
        if len(courses) > 0:
            instance.clearesult_courses.add(*courses)
        serializer = ClearesultCatalogSerializer(instance)
        return Response(serializer.data)

    def destroy(self, request, pk=None):
        """
        Delete the particular instance of catalog as per pk
        DELETE /clearesult/api/v0/catalogs/2
        """
        error, instance = validate_clearesult_catalog_pk(pk)
        if error:
            return error

        if not request.user.is_superuser:
            error = validate_catalog_update_deletion(request.user, instance)
            if error:
                return error

        instance.delete()
        return Response(
            {'detail': 'The clearesult catalog with id {} has been deleted successfully.'.format(pk)},
            status=status.HTTP_200_OK
        )


class ClearesultCourseViewset(viewsets.ViewSet):
    authentication_classes = [BasicAuthentication, SessionAuthentication, BearerAuthentication, JwtAuthentication,]
    permission_classes = [permissions.IsAuthenticated, IsAdminOrLocalAdmin]

    def list(self, request):
        """
        Return the list of available courses
        GET /clearesult/api/v0/courses/

        [
            {
                "course_name": "Testing automata course",
                "course_id": "course-v1:edx+22+2020_T122",
                "site": {
                    "id": 1,
                    "domain": "localhost:18000"
                }
            },
            ...
            ...
        ]

        """
        queryset = ClearesultCourse.objects.select_related('site')
        if not request.user.is_superuser:
            error, allowed_sites = validate_sites_for_local_admin(request.user)
            if error:
                return error
            queryset = queryset.filter(Q(site__in=allowed_sites) | Q(site=None))

        serializer = ClearesultCourseSerializer(queryset, many=True)
        return Response(serializer.data)


class SiteViewset(viewsets.ViewSet):
    authentication_classes = [BasicAuthentication, SessionAuthentication, BearerAuthentication, JwtAuthentication,]
    permission_classes = [permissions.IsAuthenticated, IsAdminOrLocalAdmin]

    def list(self, request):
        """
        Return the list of available sites
        GET /clearesult/api/v0/sites/

        [
            {
                "id": 1,
                "domain": "localhost:18000",
            }
            ...
            ...
        ]
        """
        if request.user.is_superuser:
            queryset = Site.objects.filter(name__iendswith='LMS')
        else:
            queryset = ClearesultLocalAdmin.objects.filter(
                user=request.user,
                site__name__iendswith='LMS'
            ).values('site')
            local_sites_ids = []
            for item in queryset:
                local_sites_ids.append(item.get('site'))

            queryset = Site.objects.filter(id__in=local_sites_ids)

        serializer = SiteSerializer(queryset, many=True)
        return Response(serializer.data)


class SiteLinkedObjectsListView(generics.ListAPIView):
    """
    Return a list of catalogs/users/groups linked with site_id depending upon type parameter.
    Available options for type are catalogs, groups and users

    To get a list of groups of given site:
    Get /clearesult/api/v0/site_linked_objects/groups/site_pk/
    ```
    [
        {
            "id": "1"
            "name": "group1 1",
        },
        {
            "id": "2"
            "name": "group 2",
        },
    ]
    ```

    To get a list of catalogs of given site:
    Get /clearesult/api/v0/site_linked_objects/catalogs/site_pk/
    ```
    [
        {
            "id": "1"
            "name": "catalog 1",
            "site": {
                "id": 1,
                "domain: "example.com"
            }
        },
        {
            "id": "2"
            "name": "catalog 2",
            "site": null
        },
    ]
    ```

    To get a list of users of given site:
    Get /clearesult/api/v0/site_linked_objects/users/site_pk/
    ```
    [
        {
            "id": "1"
            "username": "username1",
            "email": "username1@example.com"
        },
        {
            "id": "2"
            "username": "username2",
            "email": "username2@example.com"
        },
    ]
    ```
    """
    permission_classes = [permissions.IsAuthenticated, IsAdminOrLocalAdmin]
    authentication_classes = [BasicAuthentication, SessionAuthentication, BearerAuthentication, JwtAuthentication]
    pagination_class = None

    def get_serializer_class(self):
        object_type = self.kwargs.get('type')
        typeSerilizerMap = {
            'users': UserSerializer,
            'groups': ClearesultGroupsSerializer,
            'catalogs': ClearesultCatalogSerializer
        }
        if object_type:
            serializer_class = typeSerilizerMap.get(object_type)

        if not object_type or not serializer_class:
            raise NotFound(
                "error - site linked objects of given type doesn't exist." +
                " Available options are users, groups, catalogs")

        return serializer_class

    def get_queryset(self):
        site_pk = self.kwargs.get('site_pk')

        try:
            site = Site.objects.get(id=site_pk)
        except Site.DoesNotExist:
            raise NotFound("error - site with id doesn't exist")

        error_response, allowed_sites = validate_sites_for_local_admin(self.request.user)

        if allowed_sites and site not in allowed_sites:
            return Response(
                {'detail': 'You are not authenticated to view groups of this site.'},
                status=status.HTTP_403_FORBIDDEN
            )

        typeObjectsQuerySetMap = {
            'users': get_site_users(site),
            'groups': ClearesultGroupLinkage.objects.filter(site=site),
            'catalogs': ClearesultCatalog.objects.filter(Q(site=site) | Q(site=None)),
        }
        object_type = self.kwargs.get('type')
        query_set = typeObjectsQuerySetMap.get(object_type)
        return query_set

    def get_serializer_context(self):
        context = super(SiteLinkedObjectsListView, self).get_serializer_context()
        object_type = self.kwargs.get('type')
        if object_type == "groups":
            context.update({'fields' : ['id', 'name']})
        if object_type == "catalogs":
            context.update({'fields' : ['id', 'name', 'site']})
        return context


class ClearesultGroupViewset(viewsets.ModelViewSet):
    """
    Update Groups:

    Get /clearesult/api/v0/user_groups/
    Post /clearesult/api/v0/user_groups/

    Patch /clearesult/api/v0/user_groups/pk/
    Accept:
    ```
    {
        "name": "new name",
        "users": [1,2] //user_ids
    }
    ```

    Return:
    ```
    {
        "id": 1,
        "name": "new name",
        "site": {
            "id": 1,
            "domain": "localhost:18000",
            "name": "localhost:18000"
        },
        "users": [
            {
                "username": "ecommerce_worker",
                "email": "ecommerce_worker@example.com",
                "id": 1
            }
        ]
    }
    ```
    """
    serializer_class = ClearesultGroupsSerializer
    pagination_class = None
    permission_classes = [permissions.IsAuthenticated, IsAdminOrLocalAdmin]
    authentication_classes = [BasicAuthentication, SessionAuthentication, BearerAuthentication, JwtAuthentication]

    def get_queryset(self):
        all_groups = ClearesultGroupLinkage.objects.all()
        error_response, allowed_sites = validate_sites_for_local_admin(self.request.user)

        if allowed_sites:
            all_groups = all_groups.filter(site__in=allowed_sites)

        return all_groups

    def get_serializer_context(self):
        context = super(ClearesultGroupViewset, self).get_serializer_context()
        error_response, allowed_sites = validate_sites_for_local_admin(self.request.user)
        context.update({"allowed_sites": allowed_sites})
        return context


class ClearesultMandatoryCoursesViewset(viewsets.ModelViewSet):
    """

    GET LIST clearesult/api/v0/mandatory_courses
    [
        {
            "id": 221,
            "catalog": {
                "id": 5,
                "clearesult_courses": [
                    {
                        "id": 7,
                        "course_name": "test setttings",
                        "site": null,
                        "course_id": "course-v1:edX+test+test"
                    },
                    {
                        "id": 8,
                        "course_name": "test organzation name andy bug",
                        "site": null,
                        "course_id": "course-v1:CR+weatherization22+v1"
                    }
                ],
                "site": null,
                "name": "public catalog 1"
            },
            "mandatory_courses": [7]
        }
    ]

    PATCH clearesult/api/v0/mandatory_courses/ClearesultGroupLinkedCatalogs_id/
    {
        mandatory_courses: [1,2,3]
    }
    """

    serializer_class = ClearesultMandatoryCoursesSerializer
    queryset = ClearesultGroupLinkedCatalogs.objects.all()
    pagination_class = None
    permission_classes = [permissions.IsAuthenticated, IsAdminOrLocalAdmin]
    authentication_classes = [BasicAuthentication, SessionAuthentication, BearerAuthentication, JwtAuthentication]

    def get_serializer_context(self):
        action = self.request.data.get("action")
        context = super(ClearesultMandatoryCoursesViewset, self).get_serializer_context()
        error_response, allowed_sites = validate_sites_for_local_admin(self.request.user)
        context.update({"action": action, "allowed_sites": allowed_sites})
        return context

    def get_queryset(self):
        queryset = ClearesultGroupLinkedCatalogs.objects.all()
        error_response, allowed_sites = validate_sites_for_local_admin(self.request.user)
        if allowed_sites:
            queryset = queryset.filter(group__site__in=allowed_sites)

        return queryset


class ClearesultGroupCatalogsViewset(ClearesultGroupViewset):
    """
        GET: Just list view is being used.
        clearesult/api/v0/group_catalogs/

        [
            {
                "id": 30,
                "name": "lms group 1",
                "site": {
                    "id": 1,
                    "domain": "localhost:18000"
                },
                "catalogs": [
                    {
                        "id": 220,
                        "catalog": {
                            "id": 1,
                            "clearesult_courses": [
                                {
                                    "id": 2,
                                    "course_name": "default course 10",
                                    "site": {
                                        "id": 1,
                                        "domain": "localhost:18000"
                                    },
                                    "course_id": "course-v1:edX+default10+default10"
                                },
                                {
                                    "id": 3,
                                    "course_name": "default course 12",
                                    "site": {
                                        "id": 1,
                                        "domain": "localhost:18000"
                                    },
                                    "course_id": "course-v1:edX+def12+def12"
                                },
                                {
                                    "id": 4,
                                    "course_name": "default course 13",
                                    "site": {
                                        "id": 1,
                                        "domain": "localhost:18000"
                                    },
                                    "course_id": "course-v1:edX+def13+def13"
                                }
                            ],
                            "site": {
                                "id": 1,
                                "domain": "localhost:18000"
                            },
                            "name": "lms catalog 1"
                        },
                        "mandatory_courses": [
                            2,
                            4
                        ]
                    },
                    {
                        "id": 221,
                        "catalog": {
                            "id": 5,
                            "clearesult_courses": [
                                {
                                    "id": 7,
                                    "course_name": "test setttings",
                                    "site": null,
                                    "course_id": "course-v1:edX+test+test"
                                }
                            ],
                            "site": null,
                            "name": "public catalog 1"
                        },
                        "mandatory_courses": []
                    }
                ]
            }
        ]

    """
    def get_serializer_context(self):
        context = super(ClearesultGroupCatalogsViewset, self).get_serializer_context()
        context.update({"fields": ['id', 'name', 'site', 'catalogs']})
        return context


class ClearesultUpdateGroupCatalogsViewset(viewsets.ViewSet):
    """

    This view will do Group catalogs linkage bulk update.
    Using this we can add, remove and set multiple catalogs to multiple groups

    actions:
    add - add catalogs to given groups
    remove - remove linkage of given catalogs from given groups
    update - remove all old given groups linkage and just set the given catalogs

    POST: clearesult/api/v0/update_group_catalogs/
    {
        "action": "add/remove/update",
        "groups": [1,3,4],
        "catalogs" [4,5]
    }

    Note:
    - This serailizer is not responsible to create catalogs and groups objects. It will just add already cretaed
      catalogs to already created groups using ManyToMany relation.
    - it will not raise error if the catalogs we are trying to add in particular groups are already there.
    - similarly it will not raise error if the catalogs we are trying to remove in particular groups are not there.
    """

    pagination_class = None
    permission_classes = [permissions.IsAuthenticated, IsAdminOrLocalAdmin]
    authentication_classes = [BasicAuthentication, SessionAuthentication, BearerAuthentication, JwtAuthentication]

    def _handle_add_catalogs_action(self, groups, catalogs):
        for group in groups:
            for catalog in catalogs:
                group.catalogs.add(catalog)

    def _handle_remove_catalogs_action(self, groups, catalogs):
        for group in groups:
                group.catalogs.through.objects.filter(catalog__in=catalogs, group=group).delete()

    def _handle_update_catalogs_action(self, groups, catalogs):
        for group in groups:
            group.catalogs.set(catalogs)

    def _validate_fields(self, groups, catalogs, action):
        if not action or action not in ["add", "update", "remove"]:
            return 'action field is not valid, availble options are "add", "update" and "remove"'

        if not groups or not(type(groups) == list):
            return 'Required Field: "groups" is a required field, and must be a list.'

        try:
            [int(num) for num in groups]
        except(TypeError, ValueError):
            return 'Invalid field: "groups" must be a list of valid integers.'

        if not catalogs or not(type(catalogs) == list):
            return 'Required Field: "catalogs" is a required field, and must be a list.'

        try:
            [int(num) for num in catalogs]
        except(TypeError, ValueError):
            return 'Invalid field: "groups" must be a list of valid integers.'

    def _validate_objects(self, group_objs, catalog_objs, group_ids, catalog_ids):
        if not(len(group_objs) == len(group_ids)):
                return Response(
                {'detail': 'groups field is not valid or group with id does not exist.'},
                status=status.HTTP_403_FORBIDDEN
            )

        if not(len(catalog_objs) == len(catalog_ids)):
            return Response(
                {'detail': 'catalogs field is not valid or catalog with id does not exist.'},
                status=status.HTTP_403_FORBIDDEN
            )

        group_site = group_objs[0].site
        if not(len(group_objs.filter(site=group_site)) == len(group_objs)):
            return Response(
                {'detail': 'bulk update - groups must belong to same site.'},
                status=status.HTTP_403_FORBIDDEN
            )
        elif not(len(catalog_objs.filter(Q(site=group_site) | Q(site=None))) == len(catalog_ids)):
            return Response(
                {'detail': 'bulk update catalogs must be local catlogs of given groups or public catalogs.'},
                status=status.HTTP_403_FORBIDDEN
            )
        else:
            error_response, allowed_sites = validate_sites_for_local_admin(self.request.user)
            if allowed_sites and group_site not in allowed_sites:
                return Response(
                    {'detail': 'You are not authorized to perform action on these groups linkage.'},
                    status=status.HTTP_403_FORBIDDEN
                )

    def update(self, request):
        error = None
        group_ids = request.data.get('groups')
        catalog_ids = request.data.get('catalogs')
        action = request.data.get('action')

        error = self._validate_fields(group_ids, catalog_ids, action)
        if error:
            raise NotFound(error)

        group_objs = ClearesultGroupLinkage.objects.filter(id__in=group_ids)
        catalog_objs = ClearesultCatalog.objects.filter(id__in=catalog_ids)

        error_response = self._validate_objects(group_objs, catalog_objs, group_ids, catalog_ids)
        if error_response:
            return error_response

        action_selector = {
            'add': self._handle_add_catalogs_action,
            'remove': self._handle_remove_catalogs_action,
            'update': self._handle_update_catalogs_action
        }
        func = action_selector.get(action)
        func(group_objs, catalog_objs)

        group_serializer_data = ClearesultGroupsSerializer(
            group_objs, many=True, context = {"fields": ['id', 'name', 'site', 'catalogs']}).data
        return Response(group_serializer_data)
