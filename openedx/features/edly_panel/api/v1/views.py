from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response


@api_view(['GET'])
def get_maus(request):
    """
        For the time being just returning dummy data.
        to check the responose.
        Actual implementation would be done later.
    """
    return Response({'hello': 'brother'})
