# Generated by Django 5.1.1 on 2025-01-01 04:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('registration', '0008_remove_userprofile_spotify_autherized_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='proxy',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
