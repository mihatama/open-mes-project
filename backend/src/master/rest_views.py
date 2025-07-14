from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from .models import Item, Supplier, Warehouse # master.models を直接参照
from .forms import ItemForm, SupplierForm, WarehouseForm
from .serializers import (
    ItemSerializer, SupplierSerializer, WarehouseSerializer,
    ItemCreateUpdateSerializer, SupplierCreateUpdateSerializer, WarehouseCreateUpdateSerializer
)
from django.db.models import ProtectedError
from django.shortcuts import get_object_or_404
from django.db import transaction, IntegrityError
from django.http import HttpResponse # CSV Template View で使用
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
import csv
import io


class ItemCreateAjaxAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        item_id = request.data.get('id')
        instance = None
        if item_id:
            instance = get_object_or_404(Item, pk=item_id)
        
        form = ItemForm(request.data, instance=instance)
        if form.is_valid():
            item = form.save()
            message = '品番マスターを更新しました。' if instance else '品番マスターを登録しました。'
            return Response({'status': 'success', 'message': message, 'item_id': item.id}, status=status.HTTP_200_OK)
        else:
            return Response({'status': 'error', 'errors': form.errors}, status=status.HTTP_400_BAD_REQUEST)

class SupplierCreateAjaxAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        supplier_id = request.data.get('id')
        instance = None
        if supplier_id:
            instance = get_object_or_404(Supplier, pk=supplier_id)

        form = SupplierForm(request.data, instance=instance)
        if form.is_valid():
            supplier = form.save()
            message = 'サプライヤーマスターを更新しました。' if instance else 'サプライヤーマスターを登録しました。'
            return Response({'status': 'success', 'message': message, 'supplier_id': supplier.id}, status=status.HTTP_200_OK)
        else:
            return Response({'status': 'error', 'errors': form.errors}, status=status.HTTP_400_BAD_REQUEST)

class WarehouseCreateAjaxAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        warehouse_id = request.data.get('id') # UUID
        instance = None
        if warehouse_id:
            instance = get_object_or_404(Warehouse, pk=warehouse_id)

        form = WarehouseForm(request.data, instance=instance)
        if form.is_valid():
            warehouse = form.save()
            message = '倉庫マスターを更新しました。' if instance else '倉庫マスターを登録しました。'
            return Response({'status': 'success', 'message': message, 'warehouse_id': warehouse.id}, status=status.HTTP_200_OK)
        else:
            return Response({'status': 'error', 'errors': form.errors}, status=status.HTTP_400_BAD_REQUEST)

class ItemListAjaxAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        items = Item.objects.all()
        # The JS expects specific fields, including display versions for choices.
        # Let's manually construct the data like the old view or ensure serializer provides it.
        data = [{
            'id': item.id,
            'code': item.code,
            'name': item.name,
            'item_type': item.get_item_type_display(), # JS expects display value
            'unit': item.unit,
            'description': item.description if item.description else "",
            'default_warehouse': item.default_warehouse if item.default_warehouse else "",
            'default_location': item.default_location if item.default_location else "",
            'provision_type': item.get_provision_type_display() if item.provision_type else "" # JS expects display value
        } for item in items]
        return Response({'data': data})

class SupplierListAjaxAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        suppliers = Supplier.objects.all()
        serializer = SupplierSerializer(suppliers, many=True)
        return Response({'data': serializer.data})

class WarehouseListAjaxAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        warehouses = Warehouse.objects.all()
        serializer = WarehouseSerializer(warehouses, many=True)
        return Response({'data': serializer.data})

class ItemDetailAjaxAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk, *args, **kwargs):
        item = get_object_or_404(Item, pk=pk)
        # The form expects raw choice values, not display values for item_type, provision_type
        data = {
            'id': item.id, 'name': item.name, 'code': item.code,
            'item_type': item.item_type, # Raw value for form
            'description': item.description, 'unit': item.unit,
            'default_warehouse': item.default_warehouse, 'default_location': item.default_location,
            'provision_type': item.provision_type # Raw value for form
        }
        return Response({'status': 'success', 'data': data})

class SupplierDetailAjaxAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk, *args, **kwargs):
        supplier = get_object_or_404(Supplier, pk=pk)
        serializer = SupplierCreateUpdateSerializer(supplier) # Use serializer that matches form fields
        return Response({'status': 'success', 'data': serializer.data})

class WarehouseDetailAjaxAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk, *args, **kwargs): # pk is UUID
        warehouse = get_object_or_404(Warehouse, pk=pk)
        serializer = WarehouseCreateUpdateSerializer(warehouse) # Use serializer that matches form fields
        return Response({'status': 'success', 'data': serializer.data})

class ItemDeleteAjaxAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk, *args, **kwargs): # JS uses POST
        item = get_object_or_404(Item, pk=pk)
        item_name = item.name
        try:
            item.delete()
            return Response({'status': 'success', 'message': f'品番マスター「{item_name}」を削除しました。'})
        except ProtectedError:
            return Response({'status': 'error', 'message': 'この品番マスターは他で使用されているため削除できません。関連データを確認してください。'}, status=status.HTTP_400_BAD_REQUEST)

class SupplierDeleteAjaxAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk, *args, **kwargs): # JS uses POST
        supplier = get_object_or_404(Supplier, pk=pk)
        supplier_name = supplier.name
        try:
            supplier.delete()
            return Response({'status': 'success', 'message': f'サプライヤー「{supplier_name}」を削除しました。'})
        except ProtectedError:
            return Response({'status': 'error', 'message': 'このサプライヤーは他で使用されているため削除できません。関連データを確認してください。'}, status=status.HTTP_400_BAD_REQUEST)

class WarehouseDeleteAjaxAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk, *args, **kwargs): # JS uses POST, pk is UUID
        warehouse = get_object_or_404(Warehouse, pk=pk)
        warehouse_name = warehouse.name
        try:
            warehouse.delete()
            return Response({'status': 'success', 'message': f'倉庫「{warehouse_name}」を削除しました。'})
        except ProtectedError:
            return Response({'status': 'error', 'message': 'この倉庫は他で使用されているため削除できません。関連データを確認してください。'}, status=status.HTTP_400_BAD_REQUEST)


# --- Base CSV Import APIView ---
class BaseCSVImportAPIView(APIView):
    permission_classes = [IsAuthenticated]
    model = None
    expected_headers = []
    unique_field_csv_index = 0 
    unique_model_field = ''    
    model_verbose_name_plural = "レコード"

    def get_expected_headers(self):
        if not self.expected_headers:
            raise NotImplementedError("Subclasses must define expected_headers.")
        return self.expected_headers

    def get_model(self):
        if not self.model:
            raise NotImplementedError("Subclasses must define model.")
        return self.model

    def get_unique_model_field(self):
        if not self.unique_model_field:
            raise NotImplementedError("Subclasses must define unique_model_field.")
        return self.unique_model_field

    def process_row_data(self, row_data_dict, row_number):
        raise NotImplementedError("Subclasses must implement process_row_data.")

    def get_response_messages(self, created_count, updated_count, errors_list):
        message_parts = []
        model_name = self.model_verbose_name_plural

        if created_count > 0:
            message_parts.append(f"{created_count}件の{model_name}が新規登録されました。")
        if updated_count > 0:
            message_parts.append(f"{updated_count}件の{model_name}が更新されました。")
        
        final_message = " ".join(message_parts) if message_parts else "処理対象の有効なデータがCSVにありませんでした。"

        if errors_list:
            status_code = status.HTTP_207_MULTI_STATUS if (created_count + updated_count > 0) else status.HTTP_400_BAD_REQUEST
            response_status_str = 'partial_success' if (created_count + updated_count > 0) else 'error'
            if response_status_str == 'error':
                final_message = "CSVの処理中にエラーが発生しました。詳細はエラーリストを確認してください。"
            return Response({
                'status': response_status_str,
                'message': final_message,
                'created_count': created_count,
                'updated_count': updated_count,
                'errors': errors_list
            }, status=status_code)
        
        return Response({
            'status': 'success',
            'message': final_message,
            'created_count': created_count,
            'updated_count': updated_count
        }, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        csv_file = request.FILES.get('csv_file')
        if not csv_file:
            return Response({'status': 'error', 'message': 'CSVファイルが見つかりません。'}, status=status.HTTP_400_BAD_REQUEST)
        if not csv_file.name.endswith('.csv'):
            return Response({'status': 'error', 'message': '無効なファイル形式です。CSVファイルをアップロードしてください。'}, status=status.HTTP_400_BAD_REQUEST)

        created_count = 0
        updated_count = 0
        errors_list = []
        
        current_model = self.get_model()
        current_expected_headers = self.get_expected_headers()
        current_unique_model_field = self.get_unique_model_field()
        unique_field_csv_key = current_expected_headers[self.unique_field_csv_index]

        try:
            decoded_file = csv_file.read().decode('utf-8-sig')
            io_string = io.StringIO(decoded_file)
            reader = csv.reader(io_string)
            
            try:
                header = next(reader)
            except StopIteration:
                return Response({'status': 'error', 'message': 'CSVファイルが空です。'}, status=status.HTTP_400_BAD_REQUEST)
                
            if header != current_expected_headers:
                errors_list.append(f"CSVヘッダーが不正です。期待されるヘッダー: {', '.join(current_expected_headers)}。実際のヘッダー: {', '.join(header)}")
                return Response({'status': 'error', 'message': 'CSVファイルの形式が正しくありません。', 'errors': errors_list}, status=status.HTTP_400_BAD_REQUEST)

            rows_to_process = list(reader)
            if not rows_to_process:
                 return Response({'status': 'success', 'message': 'CSVファイルに処理するデータ行がありませんでした。', 'created_count': 0, 'updated_count': 0}, status=status.HTTP_200_OK)

            with transaction.atomic():
                for i, row_values in enumerate(rows_to_process, start=2):
                    row_specific_errors = []
                    if len(row_values) != len(current_expected_headers):
                        errors_list.append(f"行 {i}: 列数が正しくありません。期待される列数: {len(current_expected_headers)}, 実際の列数: {len(row_values)}")
                        continue 
                    
                    try:
                        row_data_dict = {current_expected_headers[j]: str(cell).strip() for j, cell in enumerate(row_values)}
                    except Exception:
                         errors_list.append(f"行 {i}: データの読み取りまたは変換に失敗しました。")
                         continue
                    
                    unique_value = row_data_dict.get(unique_field_csv_key)

                    defaults_data, validation_errors = self.process_row_data(row_data_dict, i)
                    row_specific_errors.extend(validation_errors)
                    
                    if not unique_value and not any(unique_field_csv_key in error for error in row_specific_errors):
                        row_specific_errors.append(f"{unique_field_csv_key}は必須です。")

                    if row_specific_errors:
                        errors_list.append(f"行 {i}: {'; '.join(row_specific_errors)}")
                        continue

                    try:
                        update_kwargs = {current_unique_model_field: unique_value}
                        _, created = current_model.objects.update_or_create(
                            **update_kwargs,
                            defaults=defaults_data
                        )
                        if created: created_count += 1
                        else: updated_count += 1
                    except IntegrityError as e:
                        errors_list.append(f"行 {i} ({unique_field_csv_key}: {unique_value}): データベースエラー。ユニーク制約違反やデータ長超過の可能性があります。詳細: {e}")
                    except Exception as e:
                        errors_list.append(f"行 {i} ({unique_field_csv_key}: {unique_value}): 予期せぬデータベース保存エラー - {e}")
            
            return self.get_response_messages(created_count, updated_count, errors_list)

        except UnicodeDecodeError:
            return Response({'status': 'error', 'message': 'ファイルのエンコーディングが無効です。UTF-8 (BOM付き可) を使用してください。'}, status=status.HTTP_400_BAD_REQUEST)
        except csv.Error as e:
            return Response({'status': 'error', 'message': f'CSV解析エラー: {e}'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            import traceback
            traceback.print_exc() 
            return Response({'status': 'error', 'message': f'予期せぬサーバーエラーが発生しました: {e}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# --- CSV Template and Import APIViews ---
class ItemCSVTemplateAPIView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, *args, **kwargs):
        headers = ["品番コード", "品番名", "品目タイプ", "単位", "説明", "デフォルト入庫倉庫", "デフォルト入庫棚番", "支給種別"]
        example_row = ["ITEM-001", "製品X", "product", "個", "これはサンプルです", "中央倉庫", "A-01-01", "paid"]

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(headers)
        writer.writerow(example_row)

        csv_content_bytes = output.getvalue().encode('utf-8-sig')
        response = HttpResponse(csv_content_bytes, content_type='text/csv; charset=utf-8-sig')
        response['Content-Disposition'] = 'attachment; filename="item_template.csv"'
        return response

class ItemImportCSVAPIView(BaseCSVImportAPIView):
    model = Item
    expected_headers = ["品番コード", "品番名", "品目タイプ", "単位", "説明", "デフォルト入庫倉庫", "デフォルト入庫棚番", "支給種別"]
    unique_field_csv_index = 0
    unique_model_field = 'code'
    model_verbose_name_plural = "品番マスター"

    def process_row_data(self, row_data_dict, row_number):
        errors = []
        code = row_data_dict.get("品番コード")
        name = row_data_dict.get("品番名")
        item_type_csv = row_data_dict.get("品目タイプ")
        unit_csv = row_data_dict.get("単位")
        description_csv = row_data_dict.get("説明")
        default_warehouse_csv = row_data_dict.get("デフォルト入庫倉庫")
        default_location_csv = row_data_dict.get("デフォルト入庫棚番")
        provision_type_csv = row_data_dict.get("支給種別")

        if not code: errors.append("品番コードは必須です。")
        if not name: errors.append("品番名は必須です。")
        if not item_type_csv: errors.append("品目タイプは必須です。")

        if code and name:
            # 別の品番コードで同じ品番名が既に存在するかチェック
            if Item.objects.filter(name=name).exclude(code=code).exists():
                errors.append(f"品番名 '{name}' は他の品番で既に使用されています。")
        
        valid_item_types = [choice[0] for choice in Item.ITEM_TYPE_CHOICES]
        if item_type_csv and item_type_csv not in valid_item_types:
            errors.append(f"品目タイプ '{item_type_csv}' は無効です。有効な値: {', '.join(valid_item_types)}")
        
        valid_provision_types = [choice[0] for choice in Item.PROVISION_TYPE_CHOICES]
        if provision_type_csv and provision_type_csv not in valid_provision_types and provision_type_csv != "":
            errors.append(f"支給種別 '{provision_type_csv}' は無効です。有効な値: {', '.join(valid_provision_types)} (または空)")

        if errors:
            return None, errors

        item_defaults = {
            'name': name,
            'item_type': item_type_csv,
            'unit': unit_csv if unit_csv else Item._meta.get_field('unit').default,
            'description': description_csv if description_csv else None,
            'default_warehouse': default_warehouse_csv if default_warehouse_csv else None,
            'default_location': default_location_csv if default_location_csv else None,
            'provision_type': provision_type_csv if provision_type_csv else None,
        }
        return item_defaults, errors

class SupplierCSVTemplateAPIView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, *args, **kwargs):
        headers = ["サプライヤー番号", "サプライヤー名", "担当者名", "電話番号", "メールアドレス", "住所"]
        example_row = ["SUP-001", "株式会社サンプル", "山田太郎", "03-xxxx-xxxx", "yamada@example.com", "東京都..."]

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(headers)
        writer.writerow(example_row)

        csv_content_bytes = output.getvalue().encode('utf-8-sig')
        response = HttpResponse(csv_content_bytes, content_type='text/csv; charset=utf-8-sig')
        response['Content-Disposition'] = 'attachment; filename="supplier_template.csv"'
        return response

class SupplierImportCSVAPIView(BaseCSVImportAPIView):
    model = Supplier
    expected_headers = ["サプライヤー番号", "サプライヤー名", "担当者名", "電話番号", "メールアドレス", "住所"]
    unique_field_csv_index = 0
    unique_model_field = 'supplier_number'
    model_verbose_name_plural = "サプライヤーマスター"

    def process_row_data(self, row_data_dict, row_number):
        errors = []
        supplier_number = row_data_dict.get("サプライヤー番号")
        name = row_data_dict.get("サプライヤー名")
        contact_person = row_data_dict.get("担当者名")
        phone = row_data_dict.get("電話番号")
        email = row_data_dict.get("メールアドレス")
        address = row_data_dict.get("住所")

        if not supplier_number: errors.append("サプライヤー番号は必須です。")
        if not name: errors.append("サプライヤー名は必須です。")

        if supplier_number and name:
            # 別のサプライヤー番号で同じサプライヤー名が既に存在するかチェック
            if Supplier.objects.filter(name=name).exclude(supplier_number=supplier_number).exists():
                errors.append(f"サプライヤー名 '{name}' は他のサプライヤーで既に使用されています。")
        
        if email:
            try:
                validate_email(email)
            except ValidationError:
                errors.append(f"メールアドレス '{email}' の形式が正しくありません。")

        if errors:
            return None, errors

        supplier_defaults = {
            'name': name,
            'contact_person': contact_person if contact_person else None,
            'phone': phone if phone else None,
            'email': email if email else None,
            'address': address if address else None,
        }
        return supplier_defaults, errors

class WarehouseCSVTemplateAPIView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, *args, **kwargs):
        headers = ["倉庫番号", "倉庫名", "所在地"]
        example_row = ["WH-001", "本社倉庫", "東京都..."]

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(headers)
        writer.writerow(example_row)

        csv_content_bytes = output.getvalue().encode('utf-8-sig')
        response = HttpResponse(csv_content_bytes, content_type='text/csv; charset=utf-8-sig')
        response['Content-Disposition'] = 'attachment; filename="warehouse_template.csv"'
        return response

class WarehouseImportCSVAPIView(BaseCSVImportAPIView):
    model = Warehouse
    expected_headers = ["倉庫番号", "倉庫名", "所在地"]
    unique_field_csv_index = 0
    unique_model_field = 'warehouse_number'
    model_verbose_name_plural = "倉庫マスター"

    def process_row_data(self, row_data_dict, row_number):
        errors = []
        warehouse_number = row_data_dict.get("倉庫番号")
        name = row_data_dict.get("倉庫名")
        location = row_data_dict.get("所在地")

        if not warehouse_number: errors.append("倉庫番号は必須です。")
        if not name: errors.append("倉庫名は必須です。")

        if errors:
            return None, errors

        warehouse_defaults = {
            'name': name,
            'location': location if location else None,
        }
        return warehouse_defaults, errors