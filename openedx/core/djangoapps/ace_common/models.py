from django.contrib.auth.models import User
from django.db import models


class UserMobileDevice(models.Model):
    user = models.ForeignKey(User)
    device_id = models.CharField(max_length=1024)
