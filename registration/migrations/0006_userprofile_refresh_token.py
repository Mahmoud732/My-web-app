# Generated by Django 5.1.1 on 2024-12-22 18:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('registration', '0005_userprofile_token'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='refresh_token',
            field=models.TextField(null=True, unique=True),
        ),
    ]