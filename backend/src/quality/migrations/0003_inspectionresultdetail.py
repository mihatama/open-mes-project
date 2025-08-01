# Generated by Django 5.1.7 on 2025-05-28 11:10

import django.db.models.deletion
import uuid6
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('quality', '0002_remove_inspectionitem_expected_qualitative_result_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='InspectionResultDetail',
            fields=[
                ('id', models.UUIDField(default=uuid6.uuid7, editable=False, primary_key=True, serialize=False, verbose_name='ID')),
                ('measured_value_numeric', models.FloatField(blank=True, null=True, verbose_name='測定値（定量）')),
                ('result_qualitative', models.CharField(blank=True, max_length=100, null=True, verbose_name='結果（定性）')),
                ('inspection_result', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='details', to='quality.inspectionresult', verbose_name='検査実績')),
                ('measurement_detail', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='quality.measurementdetail', verbose_name='測定・判定詳細')),
            ],
            options={
                'verbose_name': '検査実績詳細',
                'verbose_name_plural': '検査実績詳細',
                'ordering': ['inspection_result', 'measurement_detail__order'],
            },
        ),
    ]
