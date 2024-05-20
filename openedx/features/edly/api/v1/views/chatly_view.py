"""
Views for API v1.
"""
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status

from openedx.features.edly.chatly_helpers import (
    get_updated_message, handle_enable_bot, update_bot_config
)
from openedx.features.edly.models import ChatlyWidget
from openedx.features.edly.api.serializers import ChatlyWidgetSerializer
from edx_rest_framework_extensions.auth.jwt.authentication import JwtAuthentication
from edx_rest_framework_extensions.auth.session.authentication import SessionAuthenticationAllowInactiveUser
from openedx.core.lib.api.authentication import BearerAuthenticationAllowInactiveUser
from rest_framework.permissions import IsAuthenticated

class ChatlyIntegrationView(APIView):
    """
    API to handle the different bot creation, chatly linking, from studio. 
    """
    authentication_classes = (
        JwtAuthentication,
        BearerAuthenticationAllowInactiveUser,
        SessionAuthenticationAllowInactiveUser,
    )
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        GET /api/integrate/chatly/
        Tell the status of current course sync and make changes sync in backend.
        """
        widget_obj = ChatlyWidget.objects.filter(course_key=request.GET.get('course_key', '')).first()
        if widget_obj.sync_status == 2:
            return Response({
                    'error':get_updated_message(widget_obj.sync_error),
                    'status':2,          
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response({
            'status': widget_obj.sync_status
            },
            status=status.HTTP_200_OK
        )

    def post(self, request):
        """
        Post Method for enabling/disabling of bot, and modification of bot configuration values.
        api/integrate/chatly/

        """
        enable_bot = request.POST.get('enable_bot', '').lower() == "true"
        course_key = request.POST.get('course_key', '')
        widget_obj = ChatlyWidget.objects.filter(course_key=course_key)
        
        if enable_bot:
            response = handle_enable_bot(request, widget_obj)
            if response['status'] == status.HTTP_400_BAD_REQUEST:
                 return Response({
                    'error':response['message'],
                },
                status=status.HTTP_400_BAD_REQUEST
            )

            return Response(response['message'], status=response['status'])
        
        if not widget_obj.exists():
            response = handle_enable_bot(request, widget_obj)
            if response['status'] == status.HTTP_400_BAD_REQUEST:
                 return Response({
                    'error':response['message'],
                },
                status=status.HTTP_400_BAD_REQUEST
            )

            return Response(response['message'], status=response['status'])

        widget_obj= widget_obj.first()
        response = update_bot_config(request, widget_obj)

        if response['status'] == status.HTTP_400_BAD_REQUEST:
            return Response({
                    'error':response['message'],
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response(response['message'], status=response['status'])


class ChatlyWebHook(APIView):
    """
    A webhook to handle an API post call from chatly and update the status of current chatly bot. 
    """

    authentication_classes = []
    permission_classes = []

    def post(self, request):
        """
        api/chatly/web_hook/

        This method will handle the webhook from chatly, and update the task status.
        """
        if not request.data.get('course_key'):
            return Response(data='Unauthorized',  status=status.HTTP_401_UNAUTHORIZED)

        widget_obj = ChatlyWidget.objects.filter(course_key=request.data.get('course_key')).first()
        if int(request.data.get('status')) == 1:
            widget_obj.last_sync_date = widget_obj.sync_date
            widget_obj.last_sync_json = widget_obj.sync_json 

        serializer = ChatlyWidgetSerializer(
            widget_obj, 
            data={
                'allowed_directories': request.data.get('directory_id'),
                'sync_error': request.data.get('message'),
                'sync_status': request.data.get('status')
            }, 
            partial=True
        )

        if not serializer.is_valid():
            return Response(data='Unauthorized', status=status.HTTP_401_UNAUTHORIZED)

        serializer.save()
        return Response( data='Success',  status=status.HTTP_200_OK)
