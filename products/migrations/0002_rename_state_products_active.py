# Generated by Django 5.1.1 on 2024-09-17 12:26

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='products',
            old_name='state',
            new_name='active',
        ),
    ]