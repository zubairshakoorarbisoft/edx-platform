"""
Views for Clearesult V0 APIs
"""
import json
from importlib import import_module

from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.core.cache import cache
from django.db import IntegrityError
from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import generics
from rest_framework import permissions
from rest_framework import viewsets
from rest_framework import status
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework.exceptions import NotFound
from rest_framework.response import Response
from rest_framework.views import APIView

from edx_rest_framework_extensions.auth.jwt.authentication import JwtAuthentication
from openedx.features.clearesult_features.api.v0.serializers import UserCreditsProfileSerializer, ClearesultCreditProviderSerializer

from openedx.core.lib.api.authentication import BearerAuthentication
from openedx.features.clearesult_features.models import (
    ClearesultCreditProvider, UserCreditsProfile, ClearesultUserSession
)
from openedx.features.clearesult_features.api.v0.serializers import (
    UserCreditsProfileSerializer, ClearesultCreditProviderSerializer
)

class IsSelf(permissions.BasePermission):

    message = 'You are not authorized to edit this profile.'

    def has_permission(self, request, view):
        """
        User only has permission to perform the action if they are changing
        their own objects.
        """
        user_credit_profile_id = view.kwargs['pk']
        current_user = request.user

        profile = None
        try:
            profile = UserCreditsProfile.objects.get(pk=user_credit_profile_id)
        except UserCreditsProfile.DoesNotExist:
            return False
        return profile.user == current_user


class UserCreditProfileViewset(viewsets.ModelViewSet):
    authentication_classes = (JwtAuthentication, SessionAuthentication,)
    serializer_class = UserCreditsProfileSerializer
    pagination_class = None

    def get_permissions(self):
        permission_classes = []

        if self.action in ['create', 'list']:
            permission_classes = [permissions.IsAuthenticated]

        elif self.action in ['partial_update', 'destroy']:
            permission_classes = [permissions.IsAuthenticated, IsSelf]

        return [permission() for permission in permission_classes]

    def get_queryset(self):
        user = self.request.user
        return user.user_credit_profile.all()

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class ClearesultCredeitProviderListView(generics.ListAPIView):
    """
    Return a list of credit providers in the following form:

    Get /clearesult/api/v0/credit_providers/
    ```
    [
        {
            "short_code": "one",
            "name": "One",
            "id": 1
        },
        {
            "short_code": "two",
            "name": "Two",
            "id": 2
        }
    ]
    ```
    """
    queryset = ClearesultCreditProvider.objects.all()
    authentication_classes = (JwtAuthentication, SessionAuthentication,)
    permission_classes = (permissions.IsAuthenticated, )
    serializer_class = ClearesultCreditProviderSerializer
    pagination_class = None


class ClearesultLogoutView(APIView):
    authentication_classes = [BasicAuthentication, SessionAuthentication, BearerAuthentication, JwtAuthentication]
    permission_classes = [permissions.IsAuthenticated,]

    def _is_self_or_superuser(self, request, user):
        if request.user.is_superuser:
            return True

        if request.user.email == user.email:
            return True

        return False

    def post(self, request):
        email = request.data.get('email')
        if not email:
            return Response(
                {'detail': 'Please provide valid email address to logout the user.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response(
                {'detail': 'User with this email does not exist.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not self._is_self_or_superuser(request, user):
            return Response(
                {'detail': 'You are not authorized to perform this action.'},
                status=status.HTTP_403_FORBIDDEN
            )

        self._clear_session(user)

        return Response(
            {'detail': 'User with email ({}) has been logged out.'.format(user.email)},
            status=status.HTTP_200_OK
        )

    def _clear_session(self, user):
        sessions = ClearesultUserSession.objects.filter(user=user)
        session_engine = import_module(settings.SESSION_ENGINE)
        for session in sessions:
            _ = session_engine.SessionStore(session.session_key).delete()

        if sessions:
            # removing from database
            sessions.delete()

        # removing from cache
        cache.delete('clearesult_{}'.format(user.email))
