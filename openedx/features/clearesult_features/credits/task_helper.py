from datetime import datetime
from pytz import UTC
from time import time
from util.file import course_filename_prefix_generator

from lms.djangoapps.instructor_analytics.csvs import format_dictlist
from lms.djangoapps.instructor_task.api_helper import submit_task
from lms.djangoapps.instructor_task.models import ReportStore
from lms.djangoapps.instructor_task.tasks_helper.runner import TaskProgress
from lms.djangoapps.instructor_task.tasks_helper.utils import tracker_emit
from openedx.features.clearesult_features.credits.tasks import calculate_credits_csv
from openedx.features.clearesult_features.credits.utils import (
    list_user_credits_for_report,
    list_user_total_credits_for_report
)


def submit_calculate_credits_csv(request, course_key, features, task_type):
    """
    Submits a task to generate a CSV file containing information about
    invited students who have not enrolled in a given course yet.

    Raises AlreadyRunningError if said file is already being updated.
    """
    task_class = calculate_credits_csv
    task_input = {
        'features': features,
        'provider_filter': request.POST.get('provider_filter', ''),
        'csv_type': task_type
    }
    task_key = ''

    return submit_task(request, task_type, task_class, course_key, task_input, task_key)


def upload_credits_csv(_xmodule_instance_args, _entry_id, course_id, task_input, action_name):
    """
    Generate a CSV file containing information about students who have earned course credits after successful
    completion of the course which means after getting passing grades in the courses.
    """
    start_time = time()
    start_date = datetime.now(UTC)
    num_reports = 1
    task_progress = TaskProgress(action_name, num_reports, start_time)
    current_step = {'step': 'Calculating credits'}
    task_progress.update_task_state(extra_meta=current_step)

    # Compute result table and format it
    query_features = task_input.get('features')
    provider_filter = task_input.get('provider_filter')
    csv_type = task_input.get('csv_type')

    if csv_type == 'credits':
        query_features_names = [
            'Username', 'Email', 'User Provider ID (CUI)', 'Provider Name', 'Provider Code',
            'Course ID', 'Course Name', 'Earned Credits', 'Grade %', 'Grade', 'Pass Date'
        ]
        student_data = list_user_credits_for_report(course_id, provider_filter)
        csv_name = 'user_earned_credits_info'
    else:
        query_features_names = ['Username', 'Email', 'User Provider ID (CUI)', 'Provider Name', 'Total Earned Credits']
        student_data = list_user_total_credits_for_report(course_id, provider_filter)
        csv_name = 'user_accumulative_credits_info'

    if provider_filter:
        csv_name = u'{csv_name}_filter_{provider}.csv'.format(csv_name=csv_name, provider=provider_filter)

    header, rows = format_dictlist(student_data, query_features)

    task_progress.attempted = task_progress.succeeded = len(rows)
    task_progress.skipped = task_progress.total - task_progress.attempted

    rows.insert(0, query_features_names)

    current_step = {'step': 'Uploading CSV'}
    task_progress.update_task_state(extra_meta=current_step)

    # Perform the upload
    upload_credits_csv_to_report_store(rows, csv_name, course_id, start_date, False)

    return task_progress.update_task_state(extra_meta=current_step)


def upload_credits_csv_to_report_store(rows, csv_name, course_id, timestamp,
                                       course_level_report=True, config_name='GRADES_DOWNLOAD'):
    """
    Upload credits data as a CSV using ReportStore. It will not append course name in the csv file name for the
    site level reports like overall earned credits reports of students.

    Arguments:
        rows: CSV data in the following format (first column may be a
            header):
            [
                [row1_colum1, row1_colum2, ...],
                ...
            ]
        csv_name: Name of the resulting CSV
        course_id: ID of the course
    """
    report_store = ReportStore.from_config(config_name)
    if course_level_report:
        report_name = u'{course_prefix}_{csv_name}_{timestamp_str}.csv'.format(
            course_prefix=course_filename_prefix_generator(course_id),
            csv_name=csv_name,
            timestamp_str=timestamp.strftime('%Y-%m-%d-%H%M')
        )
    else:
        report_name = u'{csv_name}_{timestamp_str}.csv'.format(
            csv_name=csv_name,
            timestamp_str=timestamp.strftime('%Y-%m-%d-%H%M')
        )

    report_store.store_rows(course_id, report_name, rows)
    tracker_emit(csv_name)
