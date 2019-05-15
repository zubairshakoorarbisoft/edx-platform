""" Tasks for program enrollments """
from datetime import datetime, timedelta
import logging
from celery import task
from celery_utils.logged_task import LoggedTask

from lms.djangoapps.program_enrollments.models import ProgramEnrollment

log = logging.getLogger(__name__)


@task(base=LoggedTask)
def expire_waiting_enrollments(expiration_days):
    """
    Remove all program_enrollments and related program_course_enrollments for enrollments
    that have not been modified in <expiration_days>
    """
    expiry_date = datetime.now() - timedelta(days=expiration_days)

    program_enrollments = ProgramEnrollment.objects.filter(
        user=None,
        modified__lte=expiry_date
    ).prefetch_related('program_course_enrollments')

    for program_enrollment in program_enrollments:
        log.info(
            u'Found expired program_enrollment for program_uuid=%s',
            program_enrollment.program_uuid,
        )
        for course_enrollment in program_enrollment.program_course_enrollments.all():
            log.info(
                u'Found expired program_course_enrollment for program_uuid=%s, course_key=%s',
                program_enrollment.program_uuid,
                course_enrollment.course_key,
            )

    deleted = program_enrollments.delete()
    log.info(u'Removed %s expired records: %s', deleted[0], deleted[1])
