# Generated by Django 5.1.1 on 2024-11-08 07:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0002_product_download_file'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='download_file_version',
            field=models.CharField(default='1.0.0', max_length=6),
        ),
        migrations.AlterField(
            model_name='product',
            name='download_file',
            field=models.FileField(default='Downloads/24/09/17/file<built-in function id>.exe', upload_to='Downloads/%y/%m/%d'),
        ),
    ]
