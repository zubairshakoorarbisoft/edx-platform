from django.db import models
from django.contrib.auth.models import User


# Create your models here.
class EdlyActiveUser(models.Model):
    user = models.ForeignKey(User, db_index=True, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return '{} was active on {}.'.format(self.user.username, self.created_at)
