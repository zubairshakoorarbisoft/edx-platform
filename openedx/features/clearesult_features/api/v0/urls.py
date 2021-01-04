"""
URLs for clearesult API v0.
"""
from django.conf.urls import url

from openedx.features.clearesult_features.api.v0.views import (
    ClearesultCredeitProviderListView, UserCreditProfileViewset,
    ClearesultCatalogViewset, ClearesultCourseViewset, SiteViewset
)


app_name = 'api_v0'

urlpatterns = (
    url(
        r'^user_credit_profiles/$',
        UserCreditProfileViewset.as_view({
            'get': 'list',
            'post': 'create'
        }),
        name="user_credit_profiles_list"
    ),
    url(
        r'^user_credit_profile/(?P<pk>\d+)/$',
        UserCreditProfileViewset.as_view({
            'patch': 'partial_update',
            'delete': 'destroy'
        }),
        name="user_credit_profile_detail"
    ),
    url(
        r'^credit_providers/$',
        ClearesultCredeitProviderListView.as_view(),
        name="credit_providers_list"
    ),
    url(
        r'^courses/$',
        ClearesultCourseViewset.as_view({
            'get': 'list',
        }),
        name="clearesult_courses"
    ),
    url(
        r'^catalogs/$',
        ClearesultCatalogViewset.as_view({
            'get': 'list',
            'post': 'create'
        }),
        name="clearesult_catalogs"
    ),
    url(
        r'^catalogs/(?P<pk>\d+)',
        ClearesultCatalogViewset.as_view({
            'get': 'retrieve',
            'patch': 'partial_update',
            'delete': 'destroy'
        }),
        name="clearesult_catalog_detail"
    ),
    url(
        r'^sites/$',
        SiteViewset.as_view({
            'get': 'list'
        }),
        name="clearesult_sites"
    )
)
