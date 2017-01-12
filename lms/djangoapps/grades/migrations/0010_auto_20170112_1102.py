# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('grades', '0009_auto_20170111_1507'),
    ]

    operations = [
        migrations.AlterField(
            model_name='persistentsubsectiongrade',
            name='first_attempted',
            field=models.DateTimeField(db_index=True, null=True, blank=True),
        ),
    ]
