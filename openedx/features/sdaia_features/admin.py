from django.contrib import admin
from django.utils.safestring import mark_safe

from .models import ImageAsset


class ImageAssetAdmin(admin.ModelAdmin):
    list_display = ("title", "image_display", "description")

    def image_display(self, obj):
        return mark_safe(f'<img src="{obj.image.url}" width="50" height="50" />')

    image_display.short_description = "Image"


admin.site.register(ImageAsset, ImageAssetAdmin)
