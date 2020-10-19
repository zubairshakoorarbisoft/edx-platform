"""
Clearesult Models.
"""
from django.db import models
from opaque_keys.edx.django.models import CourseKeyField
from django.contrib.auth.models import User
from django.core.validators import MaxValueValidator, MinValueValidator

APP_LABEL = 'clearesult_features'


class ClearesultCreditProvider(models.Model):
    class Meta:
        app_label = APP_LABEL

    name = models.CharField(max_length=255, unique=True)
    short_code = models.CharField(max_length=25, unique=True)

    def __str__(self):
        return self.name


class ClearesultCourseCredit(models.Model):
    class Meta:
        app_label = APP_LABEL
        unique_together = (
            ('credit_type', 'course_id')
        )

    credit_type = models.ForeignKey(ClearesultCreditProvider, on_delete=models.CASCADE)
    credit_value = models.DecimalField(decimal_places=1, max_digits=3,
                                       validators=[MinValueValidator(0.0), MaxValueValidator(10.0)])
    course_id = CourseKeyField(max_length=255, db_index=True)

    def __str__(self):
        return str(self.course_id) + ' ' + str(self.credit_type.short_code) + ' ' + str(self.credit_value)


class UserCreditsProfile(models.Model):
    class Meta:
        app_label = APP_LABEL
        unique_together = (
            ('user', 'credit_type')
        )

    user = models.ForeignKey(User, db_index=True, on_delete=models.CASCADE)
    credit_type = models.ForeignKey(ClearesultCreditProvider, on_delete=models.CASCADE)
    credit_id = models.CharField(max_length=255)
    earned_course_credits = models.ManyToManyField(ClearesultCourseCredit, related_name='earned_credits', blank=True)

    def __str__(self):
            return str(self.user.username) + ' ' + str(self.credit_type.short_code) + ' ' + str(self.credit_id)

    def courses(self):
        return [credit.course_id for credit in self.earned_course_credits.all()]

    def earned_credits(self):
        return [credit.credit_value for credit in self.earned_course_credits.all()]

    def total_credits(self):
        total = 0.0
        for credit in self.earned_course_credits.all():
            total = total + float(credit.credit_value)
        return total


class ClearesultUserProfile(models.Model):
    class Meta:
        app_label = APP_LABEL
        verbose_name_plural = 'Clearesult user profiles'

    user = models.OneToOneField(User, unique=True, db_index=True,
                                related_name='clearesult_profile', on_delete=models.CASCADE)
    job_title = models.CharField(max_length=255, blank=True)
    company = models.CharField(max_length=255, blank=True)
    state_or_province = models.CharField(max_length=255, blank=True)
    postal_code = models.CharField(max_length=50, blank=True)

    def __str__(self):
        return 'Clearesult user profile for {}.'.format(self.user.username)
