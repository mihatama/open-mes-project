# Generated by Django 5.1.7 on 2025-08-01 05:14

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0004_modeldisplaysetting_display_name'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='modeldisplaysetting',
            name='is_visible',
        ),
        migrations.RemoveField(
            model_name='modeldisplaysetting',
            name='list_width',
        ),
    ]
