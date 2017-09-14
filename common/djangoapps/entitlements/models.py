from django.db import models
from django.contrib.auth.models import User
from student.models import CourseEnrollment
from course_modes.models import CourseMode



class CourseEntitlement(models.Model):
    """
    Represents a Student's Entitlement to a Course Run for a given Course.
    """

    """
    TODO Members/Columns
    id (id Integer)
    user_id (integer)
    root_course_id (string)
    enroll_end_date (date or string?)
    mode (string)
    enrollment_course_id (FK, from the course_enrollment table, Nullable, Integer)
    is_active (boolean)
    """

    user_id = models.ForeignKey(User)
    # TODO: Lookup the Course ID Implementation in
    # the enrollment Model and elsewhere and immitate
    # TODO: Consider replacing with an integer Foreign key and a Course Table
    root_course_id = models.CharField(max_length=250)

    enroll_end_date = models.DateTimeField(null=False)

    mode = models.CharField(default=CourseMode.DEFAULT_MODE_SLUG, max_length=100)

    enrollment_course_id = models.ForeignKey(CourseEnrollment, null=True)

    is_active = models.BooleanField(default=0)

