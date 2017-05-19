# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-05-16 09:40
from __future__ import unicode_literals

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0029_auto_20170418_0717'),
    ]

    operations = [
        migrations.AddField(
            model_name='check',
            name='last_nag',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='check',
            name='nag',
            field=models.DurationField(default=datetime.timedelta(0, 60)),
        ),
        migrations.AlterField(
            model_name='check',
            name='status',
            field=models.CharField(choices=[(b'up', b'Up'), (b'down', b'Down'), (b'new', b'New'), (b'paused', b'Paused'), (b'nag', b'Nag')], default=b'new', max_length=6),
        ),
    ]