from django.shortcuts import render, get_object_or_404
from django.views import generic, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse, HttpResponse
from django.db.models import Q, Prefetch, Sum, F, Case, When, Value, IntegerField, CharField
from django.db import transaction, IntegrityError
import csv
import io
from ..serializers import ProductionPlanSerializer, PartsUsedSerializer # シリアライザをインポート
from ..models import ProductionPlan, PartsUsed, MaterialAllocation # Changed PartsUsedRecord to PartsUsed
from ..forms import ProductionPlanDataEntryForm, PartsUsedDataEntryForm # Ensure these forms exist
from master.models import Item, Warehouse # If needed for lookups, etc.

# Placeholder for existing views if this file is new or being significantly modified.
# For example, ProductionPlanCreateAjaxView, PartsUsedCreateAjaxView, etc.
# would be here.

# Example of how existing views might look (ensure they are present)
class ProductionPlanCreateAjaxView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        # Simplified existing view logic
        form = ProductionPlanDataEntryForm(request.POST)
        if form.is_valid():
            form.save()
            return JsonResponse({'status': 'success', 'message': 'Production plan created.'})
        return JsonResponse({'status': 'error', 'errors': form.errors}, status=400)

class PartsUsedCreateAjaxView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        # Simplified existing view logic
        form = PartsUsedDataEntryForm(request.POST)
        if form.is_valid():
            form.save()
            return JsonResponse({'status': 'success', 'message': 'Parts used record created.'})
        return JsonResponse({'status': 'error', 'errors': form.errors}, status=400)

class ProductionPlanListAjaxView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        # Simplified existing view logic
        plans = ProductionPlan.objects.all().values('id', 'plan_name', 'product_code', 'planned_quantity', 'planned_start_datetime', 'status')
        return JsonResponse({'data': list(plans)})

class ProductionPlanDetailAjaxView(LoginRequiredMixin, View):
    def get(self, request, pk, *args, **kwargs):
        try:
            plan = ProductionPlan.objects.get(pk=pk)
            data = {
                'id': plan.id, 'plan_name': plan.plan_name, 'product_code': plan.product_code,
                'planned_quantity': plan.planned_quantity,
                'planned_start_datetime': plan.planned_start_datetime.isoformat() if plan.planned_start_datetime else None,
                'status': plan.status
            }
            return JsonResponse({'status': 'success', 'data': data})
        except ProductionPlan.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Production Plan not found'}, status=404)

class ProductionPlanDeleteAjaxView(LoginRequiredMixin, View):
    def post(self, request, pk, *args, **kwargs):
        try:
            plan = ProductionPlan.objects.get(pk=pk)
            plan.delete()
            return JsonResponse({'status': 'success', 'message': 'Production plan deleted.'})
        except ProductionPlan.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Production Plan not found'}, status=404)

class PartsUsedListAjaxView(LoginRequiredMixin, View):
     def get(self, request, *args, **kwargs):
        records = PartsUsed.objects.all().order_by('-used_datetime').values(
            'id', 
            'production_plan', # This is a CharField
            'part_code', 
            'warehouse',       # This is a CharField
            'quantity_used', 
            'used_datetime'
        )
        # Since production_plan and warehouse are CharFields, we access them directly.
        data = [{'production_plan': r['production_plan'], 'part_code': r['part_code'], 'warehouse': r['warehouse'], 'quantity_used': r['quantity_used'], 'used_datetime': r['used_datetime'].isoformat() if r['used_datetime'] else None, 'id': r['id']} for r in records]
        return JsonResponse({'data': data})

class PartsUsedDetailAjaxView(LoginRequiredMixin, View):
    def get(self, request, pk, *args, **kwargs):
        # Simplified
        return JsonResponse({'status': 'error', 'message': 'Not implemented'}, status=501)

class PartsUsedDeleteAjaxView(LoginRequiredMixin, View):
    def post(self, request, pk, *args, **kwargs):
        # Simplified
        return JsonResponse({'status': 'error', 'message': 'Not implemented'}, status=501)

# --- CSV Template and Import Views (Stubs) ---
class ProductionPlanCSVTemplateView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        csv_content_str = "計画名,製品コード,計画数量,計画開始日時(YYYY-MM-DD HH:MM),計画終了日時(YYYY-MM-DD HH:MM),備考,親計画ID(任意)\n計画A,PROD-001,100,2023-01-01 09:00,2023-01-01 17:00,特記事項, (空白または親計画のID)"
        # Encode to UTF-8 with BOM
        csv_content_bytes = csv_content_str.encode('utf-8-sig')
        response = HttpResponse(csv_content_bytes, content_type='text/csv; charset=utf-8-sig')
        response['Content-Disposition'] = 'attachment; filename="production_plan_template.csv"'
        return response

class ProductionPlanImportCSVView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        if not request.FILES.get('csv_file'):
            return JsonResponse({'status': 'error', 'message': 'CSVファイルがアップロードされていません。'}, status=400)

        csv_file = request.FILES['csv_file']
        
        if not csv_file.name.endswith('.csv'):
            return JsonResponse({'status': 'error', 'message': 'CSVファイルを選択してください。'}, status=400)

        success_count = 0
        error_count = 0
        errors_details = []
        production_plans_to_create_instances = [] # バリデーション済みモデルインスタンスを格納

        try:
            # UTF-8 BOM付きファイルも考慮してデコード
            decoded_file = csv_file.read().decode('utf-8-sig')
            io_string = io.StringIO(decoded_file)
            reader = csv.reader(io_string)
            
            header = next(reader) # ヘッダー行を読み込む
            expected_headers = ["計画名","製品コード","計画数量","計画開始日時(YYYY-MM-DD HH:MM)","計画終了日時(YYYY-MM-DD HH:MM)","備考","親計画ID(任意)"]
            if header != expected_headers:
                return JsonResponse({
                    'status': 'error',
                    'message': 'CSVファイルのヘッダー形式が正しくありません。テンプレートを確認してください。',
                    'errors': {'ファイル形式': [f'CSVヘッダーが不正です。期待されるヘッダー: {",".join(expected_headers)}']}
                }, status=400)

            for i, row in enumerate(reader, start=2): # データ行は2行目から
                if not any(field.strip() for field in row): # 空白行はスキップ
                    continue
                
                try:
                    # CSVの列とシリアライザのフィールドをマッピング
                    data_dict = {
                        'plan_name': row[0].strip(),
                        'product_code': row[1].strip(),
                        'planned_quantity': row[2].strip(), # 文字列のまま渡し、シリアライザで型変換とバリデーション
                        'planned_start_datetime': row[3].strip(), # 文字列のまま
                        'planned_end_datetime': row[4].strip(),   # 文字列のまま
                        'remarks': row[5].strip() if len(row) > 5 else None,
                        'production_plan': row[6].strip() if len(row) > 6 and row[6].strip() else None, # CharFieldなので文字列
                        'status': 'PENDING' # デフォルトステータスを明示的に設定
                    }

                    serializer = ProductionPlanSerializer(data=data_dict)
                    if serializer.is_valid():
                        # ProductionPlanモデルインスタンスを作成 (まだDBには保存しない)
                        # validated_dataにはForeignKeyの解決などは含まれない場合があるので、
                        # モデルのフィールドに直接マッピングする。
                        # ただし、ProductionPlanSerializerはModelSerializerなので、
                        # validated_dataはモデルフィールドに対応しているはず。
                        production_plans_to_create_instances.append(ProductionPlan(**serializer.validated_data))
                    else:
                        error_count += 1
                        errors_details.append({'row': i, 'errors': serializer.errors})

                except IndexError:
                    error_count += 1
                    errors_details.append({'row': i, 'errors': {'一般': '列の数が不足しています。テンプレートを確認してください。'}})
                except Exception as e: # 予期せぬエラー
                    error_count += 1
                    errors_details.append({'row': i, 'errors': {'一般': f'処理中に予期せぬエラーが発生しました: {str(e)}'}})

            if error_count == 0 and production_plans_to_create_instances:
                with transaction.atomic():
                    created_objects = ProductionPlan.objects.bulk_create(production_plans_to_create_instances)
                    success_count = len(created_objects)
                return JsonResponse({'status': 'success', 'message': f'{success_count}件の生産計画を正常に登録しました。'})
            elif error_count > 0:
                message = f'{error_count}件のデータにエラーが見つかりました。登録処理は行われませんでした。'
                return JsonResponse({
                    'status': 'error',
                    'message': message,
                    'errors': {'詳細': errors_details} # フロントエンドが期待する形式
                }, status=400) # Bad Request
            else: # エラーもなく、作成対象もなかった場合 (例: 空のCSVファイルやヘッダーのみのファイル)
                return JsonResponse({'status': 'error', 'message': '登録する有効なデータがCSVファイルに見つかりませんでした。'}, status=400)

        except UnicodeDecodeError:
            return JsonResponse({'status': 'error', 'message': 'ファイルのエンコーディングが不正です。UTF-8形式のファイルを使用してください。'}, status=400)
        except csv.Error as e: # csvモジュール関連のエラー
            return JsonResponse({'status': 'error', 'message': f'CSVファイルの解析中にエラーが発生しました: {str(e)}'}, status=400)
        except Exception as e: # その他の予期せぬサーバーエラー
            # サーバー側のログに詳細を記録することが重要
            print(f"Unexpected server error during CSV import: {e}") # TODO: loggingモジュールを使用する
            return JsonResponse({'status': 'error', 'message': f'予期せぬサーバーエラーが発生しました。管理者にお問い合わせください。'}, status=500)

class PartsUsedCSVTemplateView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        csv_content_str = "生産計画ID,部品コード,倉庫番号,使用数量,使用日時(YYYY-MM-DD HH:MM)\n1,PART-001,WH-001,10,2023-01-01 10:00"
        # Encode to UTF-8 with BOM
        csv_content_bytes = csv_content_str.encode('utf-8-sig')
        response = HttpResponse(csv_content_bytes, content_type='text/csv; charset=utf-8-sig')
        response['Content-Disposition'] = 'attachment; filename="parts_used_template.csv"'
        return response

class PartsUsedImportCSVView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        if not request.FILES.get('csv_file'):
            return JsonResponse({'status': 'error', 'message': 'CSVファイルがアップロードされていません。'}, status=400)

        csv_file = request.FILES['csv_file']
        
        if not csv_file.name.endswith('.csv'):
            return JsonResponse({'status': 'error', 'message': 'CSVファイルを選択してください。'}, status=400)

        success_count = 0
        error_count = 0
        errors_details = []
        parts_used_to_create_instances = [] # バリデーション済みモデルインスタンスを格納

        try:
            # UTF-8 BOM付きファイルも考慮してデコード
            decoded_file = csv_file.read().decode('utf-8-sig')
            io_string = io.StringIO(decoded_file)
            reader = csv.reader(io_string)
            
            header = next(reader) # ヘッダー行を読み込む
            # PartsUsedCSVTemplateViewで定義されているヘッダーと一致させる
            expected_headers = ["生産計画ID","部品コード","倉庫番号","使用数量","使用日時(YYYY-MM-DD HH:MM)"]
            if header != expected_headers:
                return JsonResponse({
                    'status': 'error',
                    'message': 'CSVファイルのヘッダー形式が正しくありません。テンプレートを確認してください。',
                    'errors': {'ファイル形式': [f'CSVヘッダーが不正です。期待されるヘッダー: {",".join(expected_headers)}']}
                }, status=400)

            for i, row in enumerate(reader, start=2): # データ行は2行目から
                if not any(field.strip() for field in row): # 空白行はスキップ
                    continue
                
                try:
                    # CSVの列とシリアライザのフィールドをマッピング
                    # PartsUsedCSVTemplateViewのヘッダー列順に合わせる
                    data_dict = {
                        'production_plan': row[0].strip(), # CharField
                        'part_code': row[1].strip(),       # CharField
                        'warehouse': row[2].strip(),       # CharField (null=True, blank=True)
                        'quantity_used': row[3].strip(),   # 文字列のまま渡し、シリアライザで型変換とバリデーション
                        'used_datetime': row[4].strip(),   # 文字列のまま
                        # 'remarks' はテンプレートにないため、ここではマッピングしない。
                        # Serializerはremarksフィールドを認識するが、データが提供されない場合は
                        # モデルのデフォルト値 (None) が使用される。
                    }

                    serializer = PartsUsedSerializer(data=data_dict)
                    if serializer.is_valid():
                        # PartsUsedモデルインスタンスを作成 (まだDBには保存しない)
                        parts_used_to_create_instances.append(PartsUsed(**serializer.validated_data))
                    else:
                        error_count += 1
                        errors_details.append({'row': i, 'errors': serializer.errors})

                except IndexError:
                    error_count += 1
                    errors_details.append({'row': i, 'errors': {'一般': '列の数が不足しています。テンプレートを確認してください。'}})
                except Exception as e: # 予期せぬエラー
                    error_count += 1
                    errors_details.append({'row': i, 'errors': {'一般': f'処理中に予期せぬエラーが発生しました: {str(e)}'}})

            if error_count == 0 and parts_used_to_create_instances:
                with transaction.atomic():
                    created_objects = PartsUsed.objects.bulk_create(parts_used_to_create_instances)
                    success_count = len(created_objects)
                return JsonResponse({'status': 'success', 'message': f'{success_count}件の使用部品データを正常に登録しました。'})
            elif error_count > 0:
                message = f'{error_count}件のデータにエラーが見つかりました。登録処理は行われませんでした。'
                return JsonResponse({'status': 'error', 'message': message, 'errors': {'詳細': errors_details}}, status=400) # Bad Request
            else: # エラーもなく、作成対象もなかった場合
                return JsonResponse({'status': 'error', 'message': '登録する有効なデータがCSVファイルに見つかりませんでした。'}, status=400)

        except UnicodeDecodeError:
            return JsonResponse({'status': 'error', 'message': 'ファイルのエンコーディングが不正です。UTF-8形式のファイルを使用してください。'}, status=400)
        except csv.Error as e: # csvモジュール関連のエラー
            return JsonResponse({'status': 'error', 'message': f'CSVファイルの解析中にエラーが発生しました: {str(e)}'}, status=400)
        except Exception as e: # その他の予期せぬサーバーエラー
            # サーバー側のログに詳細を記録することが重要
            import traceback # エラー追跡のためにインポート
            print(f"Unexpected server error during PartsUsed CSV import: {e}")
            print(traceback.format_exc())
            return JsonResponse({'status': 'error', 'message': f'予期せぬサーバーエラーが発生しました。管理者にお問い合わせください。'}, status=500)