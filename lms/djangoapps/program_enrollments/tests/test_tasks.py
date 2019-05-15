"""
Unit tests for program_course_enrollments tasks
"""
from datetime import timedelta
from django.test import TestCase
from django.utils import timezone
from freezegun import freeze_time
from testfixtures import LogCapture
import pytest
from lms.djangoapps.program_enrollments.models import ProgramEnrollment, ProgramCourseEnrollment
from lms.djangoapps.program_enrollments.tasks import expire_waiting_enrollments, log
from lms.djangoapps.program_enrollments.tests.factories import ProgramCourseEnrollmentFactory, ProgramEnrollmentFactory
from student.tests.factories import UserFactory


class ExpireWaitingEnrollmentsTest(TestCase):
    """ Test expire_waiting_enrollments task """
    def _setup_enrollments(self, external_user_key, user, created_date):
        with freeze_time(created_date):
            program_enrollment = ProgramEnrollmentFactory(
                user=user,
                external_user_key=external_user_key,
            )
            ProgramCourseEnrollmentFactory(
                program_enrollment=program_enrollment
            )

    def test_expire(self):
        self._setup_enrollments('student_expired_waiting', None, timezone.now() - timedelta(60))
        self._setup_enrollments('student_waiting', None, timezone.now() - timedelta(59))
        self._setup_enrollments('student_actualized', UserFactory(), timezone.now() - timedelta(90))

        expired_program_enrollment = ProgramEnrollment.objects.get(
            external_user_key='student_expired_waiting'
        )
        expired_course_enrollment = ProgramCourseEnrollment.objects.get(
            program_enrollment=expired_program_enrollment
        )

        # assert deleted enrollments are logged (without pii)
        with LogCapture(log.name) as log_capture:
            expire_waiting_enrollments(60)

            program_enrollment_message_tmpl = u'Found expired program_enrollment for program_uuid={}'
            course_enrollment_message_tmpl = (
                u'Found expired program_course_enrollment for program_uuid={}, course_key={}'
            )

            log_capture.check(
                (
                    log.name,
                    'INFO',
                    program_enrollment_message_tmpl.format(expired_program_enrollment.program_uuid)
                ),
                (
                    log.name,
                    'INFO',
                    course_enrollment_message_tmpl.format(
                        expired_program_enrollment.program_uuid,
                        expired_course_enrollment.course_key
                    )
                ),
                (
                    log.name,
                    'INFO',
                    u'Removed 2 expired records:'
                    u' {u\'program_enrollments.ProgramCourseEnrollment\': 1,'
                    u' u\'program_enrollments.ProgramEnrollment\': 1}'
                ),
            )

        program_enrollments = ProgramEnrollment.objects.all()
        program_course_enrollments = ProgramCourseEnrollment.objects.all()

        # assert expired records no longer exist
        with pytest.raises(ProgramEnrollment.DoesNotExist):
            program_enrollments.get(external_user_key='student_expired_waiting')
        self.assertEqual(len(program_course_enrollments), 2)

        # assert fresh waiting records are not affected
        waiting_enrollment = program_enrollments.get(external_user_key='student_waiting')
        self.assertEqual(len(waiting_enrollment.program_course_enrollments.all()), 1)

        # assert actualized enrollments are not affected
        actualized_enrollment = program_enrollments.get(external_user_key='student_actualized')
        self.assertEqual(len(actualized_enrollment.program_course_enrollments.all()), 1)

    def test_expire_none(self):
        """ Asserts no exceptions are thrown if no enrollments are found """
        expire_waiting_enrollments(60)
        self.assertEqual(len(ProgramEnrollment.objects.all()), 0)
