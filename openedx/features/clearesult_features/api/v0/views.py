"""
Views for Clearesult V0 APIs
"""
from rest_framework import generics
from rest_framework import permissions
from rest_framework import viewsets
from rest_framework.authentication import SessionAuthentication

from edx_rest_framework_extensions.auth.jwt.authentication import JwtAuthentication

from openedx.features.clearesult_features.models import ClearesultCreditProvider, UserCreditsProfile
from openedx.features.clearesult_features.api.v0.serializers import UserCreditsProfileSerializer, ClearesultCreditProviderSerializer


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
        return user.usercreditsprofile_set.all()

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
