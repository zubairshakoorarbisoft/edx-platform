"""
Clearesult Models.
"""

from django.db import models
from opaque_keys.edx.django.models import CourseKeyField
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from django.core.validators import MaxValueValidator, MinValueValidator


class ClearesultCreditProvider(models.Model):
    class Meta:
        app_label = 'clearesult_features'

    name = models.CharField(max_length=255, unique=True)
    short_code = models.CharField(max_length=25, unique=True)

    def __str__(self):
        return self.name


class ClearesultCourseCredit(models.Model):
    class Meta:
        app_label = 'clearesult_features'
        unique_together = (
            ('credit_type', 'course_id')
        )

    credit_type = models.ForeignKey(ClearesultCreditProvider, on_delete=models.CASCADE)
    credit_value = models.DecimalField(decimal_places=1, max_digits=3, validators=[MinValueValidator(0.0), MaxValueValidator(10.0)])
    course_id = CourseKeyField(max_length=255, db_index=True)

    def __str__(self):
        return str(self.course_id) + ' ' + str(self.credit_type.short_code) + ' ' + str(self.credit_value)


class UserCreditsProfile(models.Model):
    class Meta:
        app_label = 'clearesult_features'
        unique_together = (
            ('user', 'credit_type')
        )

    user = models.ForeignKey(User, db_index=True, on_delete=models.CASCADE)
    credit_type = models.ForeignKey(ClearesultCreditProvider, on_delete=models.CASCADE)
    credit_id = models.CharField(max_length=255)
    earned_course_credits = models.ManyToManyField(ClearesultCourseCredit, related_name='earned_credits', blank=True)

    def __str__(self):
            return str(self.user.username) + ' ' + str(self.credit_type.short_code) + ' ' + str(self.credit_id)
