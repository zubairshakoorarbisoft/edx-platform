"""
Storage backend for private LMS bucket.
"""
from __future__ import absolute_import

from django.conf import settings
from django.core.files.storage import get_storage_class
from storages.backends.s3boto import S3BotoStorage
from storages.utils import setting


class PrivateS3Storage(S3BotoStorage):  # pylint: disable=abstract-method
    """
    S3 backend for private files.
    """

    def __init__(self):
        bucket = setting('PRIVATE_LMS_BUCKET', settings.AWS_STORAGE_BUCKET_NAME)
        custom_domain = '{}.s3.amazonaws.com'.format(bucket)
        super(PrivateS3Storage, self).__init__(bucket=bucket, custom_domain=custom_domain, querystring_auth=True)

# pylint: disable=invalid-name
private_lms_storage = get_storage_class(settings.PRIVATE_LMS_STORAGE)()
