# Generated by Django 5.1.1 on 2024-10-26 11:47

import datetime
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('checkout', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='created_at',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
        migrations.AddField(
            model_name='order',
            name='expires_at',
            field=models.DateTimeField(default=datetime.datetime(2024, 10, 28, 11, 47, 25, 613407, tzinfo=datetime.timezone.utc)),
        ),
    ]