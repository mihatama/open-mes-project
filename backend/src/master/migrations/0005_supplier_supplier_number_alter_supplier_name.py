# Generated by Django 5.1.7 on 2025-06-12 01:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('master', '0004_item_default_location_item_default_warehouse_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='supplier',
            name='supplier_number',
            field=models.CharField(default=123, max_length=50, unique=True, verbose_name='サプライヤー番号'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='supplier',
            name='name',
            field=models.CharField(max_length=255, verbose_name='サプライヤー名'),
        ),
    ]
