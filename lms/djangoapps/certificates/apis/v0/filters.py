import django_filters
from lms.djangoapps.certificates.models import GeneratedCertificate


class GeneratedCertificateFilter(django_filters.FilterSet):
    created_date = django_filters.DateFilter(field_name='created_date', lookup_expr='date')
    date_gt = django_filters.DateFilter(field_name='created_date', lookup_expr='gt')
    date_lt = django_filters.DateFilter(field_name='created_date', lookup_expr='lt')

    class Meta:
        model = GeneratedCertificate
        fields = ['created_date', 'date_gt', 'date_lt']
