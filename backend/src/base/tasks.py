from celery import shared_task
from celery.exceptions import SoftTimeLimitExceeded
from celery.result import AsyncResult
from django.apps import apps
from django.db import transaction, IntegrityError, models
from django.utils import timezone
import csv
import io
import os
from datetime import datetime

from .models import CsvColumnMapping, AsyncTask, DATA_TYPE_MODEL_MAPPING

@shared_task(bind=True)
def import_csv_task(self, data_type, file_path):
    task_id = self.request.id
    try:
        task = AsyncTask.objects.get(task_id=task_id)
        task.status = 'STARTED'
        task.save()

        mappings = CsvColumnMapping.objects.filter(data_type=data_type, is_active=True).order_by('order')
        if not mappings.exists():
            raise Exception(f'"{data_type}" に有効なCSVマッピング設定がありません。')

        model_string = DATA_TYPE_MODEL_MAPPING.get(data_type)
        app_label, model_name = model_string.split('.')
        model = apps.get_model(app_label=app_label, model_name=model_name)

        expected_headers = [m.csv_header for m in mappings]
        header_to_model_map = {m.csv_header: m.model_field_name for m in mappings}
        update_keys_model = [m.model_field_name for m in mappings if m.is_update_key]

        if not update_keys_model:
            raise Exception('CSVインポートのための上書きキーがCSVマッピング設定で指定されていません。')

        with open(file_path, 'r', encoding='utf-8-sig') as f:
            content = f.read()
        
        # ファイルの行数をカウントしてtotalを設定
        total_rows = len(content.splitlines()) - 1 # ヘッダーを除く
        task.total = total_rows
        task.save()

        io_string = io.StringIO(content)
        reader = csv.DictReader(io_string)

        created_count = 0
        updated_count = 0
        errors_list = []

        with transaction.atomic():
            for i, row in enumerate(reader, start=1):
                if AsyncResult(self.request.id).state == 'REVOKED':
                    task.status = 'REVOKED'
                    task.save()
                    os.remove(file_path)
                    return {'status': 'REVOKED', 'message': 'タスクがキャンセルされました。'}

                model_data = {}
                row_specific_errors = []

                for csv_header, model_field_name in header_to_model_map.items():
                    value = row.get(csv_header, '').strip()
                    if not value:
                        model_data[model_field_name] = None
                        continue
                    try:
                        field_obj = model._meta.get_field(model_field_name)
                        if isinstance(field_obj, (models.DateTimeField, models.DateField)):
                            parsed_date = None
                            for fmt in ('%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M', '%Y/%m/%d %H:%M:%S', '%Y/%m/%d %H:%M', '%Y-%m-%d', '%Y/%m/%d'):
                                try:
                                    parsed_date = datetime.strptime(value, fmt)
                                    break
                                except ValueError: continue
                            if parsed_date is None: raise ValueError("対応する日付形式ではありません。")
                            model_data[model_field_name] = parsed_date.date() if isinstance(field_obj, models.DateField) else parsed_date
                        elif isinstance(field_obj, (models.IntegerField, models.PositiveIntegerField)):
                            model_data[model_field_name] = int(float(value))
                        elif isinstance(field_obj, models.BooleanField):
                            model_data[model_field_name] = value.lower() in ['true', '1', 'yes', 't', 'はい']
                        else:
                            model_data[model_field_name] = value
                    except (ValueError, TypeError) as e:
                        row_specific_errors.append(f"フィールド '{csv_header}' の値 '{value}' は型が不正です: {e}")
                
                if row_specific_errors:
                    errors_list.append(f"行 {i+1}: {'; '.join(row_specific_errors)}")
                    continue

                update_kwargs = {key: model_data.pop(key) for key in update_keys_model if key in model_data and model_data[key] is not None}
                if len(update_kwargs) != len(update_keys_model):
                    errors_list.append(f"行 {i+1}: 上書きキー ({', '.join(update_keys_model)}) の値が空、または見つかりません。")
                    continue

                try:
                    defaults_data = {k: v for k, v in model_data.items() if v is not None}
                    _, created = model.objects.update_or_create(**update_kwargs, defaults=defaults_data)
                    if created: created_count += 1
                    else: updated_count += 1
                except (IntegrityError, Exception) as e:
                    errors_list.append(f"行 {i+1} ({update_kwargs}): データベース保存エラー - {e}")
                
                task.progress = i
                task.save(update_fields=['progress', 'updated_at'])

        task.status = 'SUCCESS' if not errors_list else 'FAILURE'
        task.result = {'created': created_count, 'updated': updated_count, 'errors': errors_list}
        task.progress = total_rows
        task.save()

    except SoftTimeLimitExceeded:
        task.status = 'FAILURE'
        task.result = {'error': 'タイムアウトしました。'}
        task.save()
    except Exception as e:
        task.status = 'FAILURE'
        task.result = {'error': str(e)}
        task.save()
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)
