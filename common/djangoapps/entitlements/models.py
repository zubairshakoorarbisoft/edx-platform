from django.db import models
from django.contrib.auth.models import User
from student.models import CourseEnrollment
from course_modes.models import CourseMode


class CourseEntitlement(models.Model):
    """
    Represents a Student's Entitlement to a Course Run for a given Course.
    """

    user_id = models.ForeignKey(User)
    # TODO: Lookup the Course ID Implementation in
    # the enrollment Model and elsewhere and immitate
    # TODO: Consider replacing with an integer Foreign key and a Course Table
    root_course_id = models.CharField(max_length=250)

    enroll_end_date = models.DateTimeField(null=False)

    mode = models.CharField(default=CourseMode.DEFAULT_MODE_SLUG, max_length=100)

    enrollment_course_id = models.ForeignKey(CourseEnrollment, null=True)

    is_active = models.BooleanField(default=1)

    @classmethod
    def entitlements_for_user(self, username):
        # TODO: Update to use the user provided
        user = User.objects.get(username=username)
        return self.objects.filter(user_id=user)
