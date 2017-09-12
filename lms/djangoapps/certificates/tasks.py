from celery import task
from logging import getLogger

from celery_utils.logged_task import LoggedTask
from celery_utils.persist_on_failure import PersistOnFailureTask
from django.contrib.auth.models import User
from lms.djangoapps.verify_student.models import SoftwareSecurePhotoVerification
from opaque_keys.edx.keys import CourseKey

from .api import generate_user_certificates

logger = getLogger(__name__)


class _BaseCertificateTask(PersistOnFailureTask, LoggedTask):  # pylint: disable=abstract-method
    """
    Include persistence features, as well as logging of task invocation.
    """
    abstract = True


@task(base=_BaseCertificateTask, bind=True, default_retry_delay=30, max_retries=2)
def generate_certificate(self, **kwargs):
    """
    Generates a certificate for a single user.

    kwargs:
        - student: The student for whom to generate a certificate.
        - course_key: The course key for the course that the student is
            receiving a certificate in.
        - expected_verification_status: Either 'approved' or None. Passed in
            from _listen_for_track_change, which runs when a learner's
            verification status is changed to verified, thus kicking off a
            certificate generation task. When the status has changed, we
            double check that the actual verification status is as expected
            before generating a certificate, in the off chance that the
            database has not yet updated with the user's new verification
            status.
    """
    student = User.objects.get(id=kwargs.pop('student'))
    course_key = CourseKey.from_string(kwargs.pop('course_key'))
    expected_verification_status = kwargs.pop('expected_verification_status', None)
    if expected_verification_status:
        actual_verification_status, _ = SoftwareSecurePhotoVerification.user_status(student)
        if expected_verification_status != actual_verification_status:
            self.retry(kwargs=kwargs)
    generate_user_certificates(student=student, course_key=course_key, **kwargs)
