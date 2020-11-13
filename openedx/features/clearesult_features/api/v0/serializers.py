"""
Serializers for Clearesult v0 APIs.
"""
from django.db.models import fields
from rest_framework import serializers

from openedx.features.clearesult_features.models import UserCreditsProfile, ClearesultCreditProvider


class UserCreditsProfileSerializer(serializers.ModelSerializer):
    credit_type_details = serializers.SerializerMethodField()

    def get_credit_type_details(self, obj):
        return {
            'name': obj.credit_type.name,
            'short_code': obj.credit_type.short_code,
        }

    class Meta:
        model = UserCreditsProfile
        fields = ('id', 'credit_type', 'credit_id', 'credit_type_details')
        read_only_fields = ('credit_type_details', 'id')
        write_only_fields = ('user',)


class ClearesultCreditProviderSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClearesultCreditProvider
        fields = ('short_code', 'name', 'id')
        read_only_fields = ('id', )
