# Generated by Django 5.1.7 on 2025-05-28 11:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('production', '0004_partsused_warehouse'),
    ]

    operations = [
        migrations.AddField(
            model_name='workprogress',
            name='actual_reported_quantity',
            field=models.PositiveIntegerField(blank=True, null=True, verbose_name='実績報告数量 (総生産数)'),
        ),
        migrations.AddField(
            model_name='workprogress',
            name='defective_reported_quantity',
            field=models.PositiveIntegerField(blank=True, null=True, verbose_name='不良報告数量'),
        ),
        migrations.AlterField(
            model_name='workprogress',
            name='quantity_completed',
            field=models.PositiveIntegerField(default=0, verbose_name='完了数量 (良品数)'),
        ),
    ]
