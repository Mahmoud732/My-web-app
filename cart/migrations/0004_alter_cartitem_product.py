# Generated by Django 5.1.1 on 2024-11-08 06:18

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cart', '0003_alter_cart_user_alter_cartitem_quantity'),
        ('product', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='cartitem',
            name='product',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='product.product'),
        ),
    ]