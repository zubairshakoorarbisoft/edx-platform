from django.db import models
from django.conf import settings
from storages.backends.s3boto3 import S3Boto3Storage


class ImageAsset(models.Model):
    title = models.CharField(max_length=255)
    image = models.ImageField(
        upload_to="image_assets/",
        storage=S3Boto3Storage(bucket_name=settings.ASSET_BUCKET),
    )
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.title
