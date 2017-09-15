# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('student', '0012_sociallink'),
    ]

    operations = [
        migrations.CreateModel(
            name='CourseEntitlement',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('root_course_id', models.CharField(max_length=250)),
                ('enroll_end_date', models.DateTimeField()),
                ('mode', models.CharField(default=b'audit', max_length=100)),
                ('is_active', models.BooleanField(default=1)),
                ('enrollment_course_id', models.ForeignKey(to='student.CourseEnrollment', null=True)),
                ('user_id', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
