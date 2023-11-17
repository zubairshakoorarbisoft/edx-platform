"""
Paginators for the course enrollment related views.
"""


from rest_framework.pagination import CursorPagination, PageNumberPagination


class CourseEnrollmentsApiListPagination(CursorPagination):
    """
    Paginator for the Course enrollments list API.
    """
    page_size = 100
    page_size_query_param = 'page_size'
    max_page_size = 100
    page_query_param = 'page'


class UsersCourseEnrollmentsApiPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100
    page_query_param = 'page'
