from functools import partial

from celery import task
from django.utils.translation import ugettext_noop

from lms.djangoapps.instructor_task.tasks_base import BaseInstructorTask
from lms.djangoapps.instructor_task.tasks_helper.runner import run_main_task
from openedx.features.clearesult_features.credits import task_helper


@task(base=BaseInstructorTask)
def calculate_credits_csv(entry_id, xmodule_instance_args):
    """
    Compute information about the students who have earned course credits
    on course completion and upload the CSV to an S3 bucket for download.
    """
    # Translators: This is a past-tense verb that is inserted into task progress messages as {action}.
    action_name = ugettext_noop('generated')
    task_fn = partial(task_helper.upload_credits_csv, xmodule_instance_args)
    return run_main_task(entry_id, task_fn, action_name)
