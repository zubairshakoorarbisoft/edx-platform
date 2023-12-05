"""
A common module for managing exceptions. Helps to avoid circular references
"""


class AssetNotFoundException(Exception):
    """
    Raised when asset not found
    """


class AssetSizeTooLargeException(Exception):
    """
    Raised when the size of an uploaded asset exceeds the maximum size limit.
    """


class InvalidFileTypeException(Exception):
    """
    Raised when the type of file is not included in mimetypes
    """