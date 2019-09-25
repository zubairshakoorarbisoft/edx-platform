# -*- coding: utf-8 -*-
from django.test import TestCase
from .models import EdlyActiveUser
from django.contrib.auth.models import User
from django.utils import timezone


class EdlyActiveUserModelTest(TestCase):

    def setUp(self):
        self.user = User.objects.create(username='test@example.com', password='test_password')
        EdlyActiveUser.objects.create(user=self.user)

    def test_string_representaion(self):
        active_user = EdlyActiveUser.objects.filter(user=self.user, created_at__date=timezone.now().date())
        self.assertIn('{} was active on {}'.format(self.user.username, timezone.now().date()), str(active_user))
