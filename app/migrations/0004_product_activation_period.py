# Generated by Django 5.1.1 on 2024-10-30 09:51

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0003_contactmessage'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='activation_period',
            field=models.DurationField(default=datetime.timedelta(seconds=7200)),
        ),
    ]
