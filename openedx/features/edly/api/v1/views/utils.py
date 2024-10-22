from rest_framework.response import Response


def error_response(message, status_code):
    """
    Generate an error response with the given message and status code.
    """
    return Response({'detail': message}, status=status_code)
