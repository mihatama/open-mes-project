from django.shortcuts import render
from django.views import View
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction, IntegrityError
from ..models import PurchaseOrder
from datetime import datetime

import csv
import io

# Create your views here.

# --- CSV Template and Import Views (Stubs) for Purchase Orders ---
class PurchaseOrderCSVTemplateView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        csv_content_str = "発注番号,品番コード,倉庫番号,発注数量,入荷予定日(YYYY-MM-DD),サプライヤー名,便番号\nPO-001,ITEM-001,WH-001,100,2023-01-01,株式会社サンプル,DELIVERY-001"
        # Encode to UTF-8 with BOM
        csv_content_bytes = csv_content_str.encode('utf-8-sig')
        response = HttpResponse(csv_content_bytes, content_type='text/csv; charset=utf-8-sig')
        response['Content-Disposition'] = 'attachment; filename="purchase_order_template.csv"'
        return response

class PurchaseOrderImportCSVView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        csv_file = request.FILES.get('csv_file')
        if not csv_file:
            return JsonResponse({'status': 'error', 'message': 'CSVファイルが見つかりません。'}, status=400)

        if not csv_file.name.endswith('.csv'):
            return JsonResponse({'status': 'error', 'message': '無効なファイル形式です。CSVファイルをアップロードしてください。'}, status=400)

        created_count = 0
        updated_count = 0
        errors_list = []

        try:
            decoded_file = csv_file.read().decode('utf-8-sig')
            io_string = io.StringIO(decoded_file)
            reader = csv.reader(io_string)

            try:
                header = next(reader)
            except StopIteration: # Empty file
                return JsonResponse({'status': 'error', 'message': 'CSVファイルが空です。'}, status=400)

            expected_headers = ["発注番号", "品番コード", "倉庫番号", "発注数量", "入荷予定日(YYYY-MM-DD)", "サプライヤー名", "便番号"]
            if header != expected_headers:
                errors_list.append(f"CSVヘッダーが不正です。期待されるヘッダー: {', '.join(expected_headers)}。実際のヘッダー: {', '.join(header)}")
                return JsonResponse({'status': 'error', 'message': 'CSVファイルの形式が正しくありません。', 'errors': errors_list}, status=400)

            rows_to_process = list(reader)
            if not rows_to_process:
                 return JsonResponse({'status': 'success', 'message': 'CSVファイルに処理するデータ行がありませんでした。', 'created_count': 0, 'updated_count': 0})

            with transaction.atomic():
                for i, row in enumerate(rows_to_process, start=2): # start=2 for 1-based data row index
                    row_specific_errors = []
                    if len(row) != len(expected_headers):
                        errors_list.append(f"行 {i}: 列数が正しくありません。期待される列数: {len(expected_headers)}, 実際の列数: {len(row)}")
                        continue
                    
                    try:
                        order_number_csv, part_number_csv, warehouse_csv, quantity_csv, expected_arrival_csv, supplier_csv, shipment_number_csv = [str(cell).strip() for cell in row]
                    except Exception:
                         errors_list.append(f"行 {i}: データの読み取りまたは変換に失敗しました。")
                         continue

                    if not order_number_csv: row_specific_errors.append("発注番号は必須です。")
                    if not quantity_csv: row_specific_errors.append("発注数量は必須です。")

                    parsed_quantity = None
                    if quantity_csv:
                        try:
                            parsed_quantity = int(quantity_csv)
                            if parsed_quantity <= 0:
                                row_specific_errors.append("発注数量は正の整数である必要があります。")
                        except ValueError:
                            row_specific_errors.append("発注数量が有効な数値ではありません。")
                    
                    parsed_expected_arrival = None
                    if expected_arrival_csv:
                        try:
                            # Assuming YYYY-MM-DD format from CSV template
                            parsed_expected_arrival = datetime.strptime(expected_arrival_csv, '%Y-%m-%d').date()
                        except ValueError:
                            row_specific_errors.append(f"入荷予定日 '{expected_arrival_csv}' の形式が正しくありません。YYYY-MM-DD形式で入力してください。")

                    if row_specific_errors:
                        errors_list.append(f"行 {i}: {'; '.join(row_specific_errors)}")
                        continue

                    po_data = {
                        'part_number': part_number_csv if part_number_csv else None,
                        'warehouse': warehouse_csv if warehouse_csv else None,
                        'quantity': parsed_quantity,
                        'expected_arrival': parsed_expected_arrival,
                        'supplier': supplier_csv if supplier_csv else None,
                        'shipment_number': shipment_number_csv if shipment_number_csv else None,
                        # 'item', 'product_name', 'location' etc. will be default or null
                    }

                    try:
                        _, created = PurchaseOrder.objects.update_or_create(order_number=order_number_csv, defaults=po_data)
                        if created: created_count += 1
                        else: updated_count += 1
                    except IntegrityError as e:
                        errors_list.append(f"行 {i} (発注番号: {order_number_csv}): データベースエラー。ユニーク制約違反（発注番号が重複している等）やデータ長超過の可能性があります。詳細: {e}")
                    except Exception as e:
                        errors_list.append(f"行 {i} (発注番号: {order_number_csv}): 予期せぬデータベース保存エラー - {e}")
            
            message_parts = []
            if created_count > 0: message_parts.append(f"{created_count}件の入庫予定が新規登録されました。")
            if updated_count > 0: message_parts.append(f"{updated_count}件の入庫予定が更新されました。")
            final_message = " ".join(message_parts) if message_parts else "処理対象の有効なデータがCSVにありませんでした。"

            if errors_list:
                status_code = 207 if (created_count + updated_count > 0) else 400
                response_status = 'partial_success' if (created_count + updated_count > 0) else 'error'
                if response_status == 'error': final_message = "CSVの処理中にエラーが発生しました。詳細はエラーリストを確認してください。"
                return JsonResponse({'status': response_status, 'message': final_message, 'created_count': created_count, 'updated_count': updated_count, 'errors': errors_list}, status=status_code)
            
            return JsonResponse({'status': 'success', 'message': final_message, 'created_count': created_count, 'updated_count': updated_count})

        except UnicodeDecodeError:
            return JsonResponse({'status': 'error', 'message': 'ファイルのエンコーディングが無効です。UTF-8 (BOM付き可) を使用してください。'}, status=400)
        except csv.Error as e:
            return JsonResponse({'status': 'error', 'message': f'CSV解析エラー: {e}'}, status=400)
        except Exception as e:
            import traceback
            traceback.print_exc() 
            return JsonResponse({'status': 'error', 'message': f'予期せぬサーバーエラーが発生しました: {e}'}, status=500)
