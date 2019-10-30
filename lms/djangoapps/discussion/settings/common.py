"""Common environment variables unique to the discussion plugin."""


def plugin_settings(settings):
    """Settings for the discussions plugin. """
    settings.FEATURES['ALLOW_HIDING_DISCUSSION_TAB'] = False
    settings.DISCUSSION_SETTINGS = {
        'MAX_COMMENT_DEPTH': 2,
        'MAX_UPLOAD_FILE_SIZE': 5 * 1024 * 1024,  # result in bytes
        'ALLOWED_UPLOAD_FILE_TYPES': (
            '.jpg', '.jpeg', '.gif', '.bmp', '.png', '.tiff', '.pdf', '.doc', '.docx',
        ),
        'COURSE_PUBLISH_TASK_DELAY': 30,
    }
