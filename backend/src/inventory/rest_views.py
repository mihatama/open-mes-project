from rest_framework import status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination # PageNumberPagination は StandardResultsSetPagination で使用
from rest_framework.views import APIView
from .serializers import (PurchaseOrderSerializer, InventorySerializer, StockMovementSerializer, SalesOrderSerializer, AllocateInventoryForSalesOrderRequestSerializer)
from .models import PurchaseOrder, Inventory, StockMovement, SalesOrder # SalesOrderモデルをインポート
from django.http import JsonResponse # JsonResponse をインポート
from django.db import transaction, IntegrityError # トランザクションのためにインポート # Qオブジェクトをインポートして複雑なクエリを構築
from django.db.models import Q, F # Fオブジェクトをインポート
from django.shortcuts import get_object_or_404 # オブジェクト取得のためにインポート
from django.db.models import ProtectedError # Import ProtectedError
from django.http import HttpResponse
import csv
import io
from datetime import datetime

# DRFのページネーションクラスを定義 (共通で利用可能)
class StandardResultsSetPagination(PageNumberPagination):
    page_size = 25  # 1ページあたりのデフォルト件数を25に変更（適宜調整してください）
    page_size_query_param = 'page_size' # クライアントが1ページあたりの件数を指定するためのクエリパラメータ
    max_page_size = 1000 # クライアントが指定できる1ページあたりの最大件数

    def get_paginated_response(self, data):
        return Response({
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'count': self.page.paginator.count,
            'total_pages': self.page.paginator.num_pages,
            'current_page': self.page.number,
            'page_size': self.get_page_size(self.request),
            'results': data
        })

# --- CSV Template and Import Views for Purchase Orders ---
class PurchaseOrderCSVTemplateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        csv_content_str = "発注番号,品番コード,倉庫番号,発注数量,入荷予定日(YYYY-MM-DD),サプライヤー名,便番号\nPO-001,ITEM-001,WH-001,100,2023-01-01,株式会社サンプル,DELIVERY-001"
        # Encode to UTF-8 with BOM
        csv_content_bytes = csv_content_str.encode('utf-8-sig')
        response = HttpResponse(csv_content_bytes, content_type='text/csv; charset=utf-8-sig')
        response['Content-Disposition'] = 'attachment; filename="purchase_order_template.csv"'
        return response

class PurchaseOrderImportCSVView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        csv_file = request.FILES.get('csv_file')
        if not csv_file:
            return Response({'status': 'error', 'message': 'CSVファイルが見つかりません。'}, status=status.HTTP_400_BAD_REQUEST)

        if not csv_file.name.endswith('.csv'):
            return Response({'status': 'error', 'message': '無効なファイル形式です。CSVファイルをアップロードしてください。'}, status=status.HTTP_400_BAD_REQUEST)

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
                return Response({'status': 'error', 'message': 'CSVファイルが空です。'}, status=status.HTTP_400_BAD_REQUEST)

            expected_headers = ["発注番号", "品番コード", "倉庫番号", "発注数量", "入荷予定日(YYYY-MM-DD)", "サプライヤー名", "便番号"]
            if header != expected_headers:
                errors_list.append(f"CSVヘッダーが不正です。期待されるヘッダー: {', '.join(expected_headers)}。実際のヘッダー: {', '.join(header)}")
                return Response({'status': 'error', 'message': 'CSVファイルの形式が正しくありません。', 'errors': errors_list}, status=status.HTTP_400_BAD_REQUEST)

            rows_to_process = list(reader)
            if not rows_to_process:
                 return Response({'status': 'success', 'message': 'CSVファイルに処理するデータ行がありませんでした。', 'created_count': 0, 'updated_count': 0})

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
                status_code = status.HTTP_207_MULTI_STATUS if (created_count + updated_count > 0) else status.HTTP_400_BAD_REQUEST
                response_status_str = 'partial_success' if (created_count + updated_count > 0) else 'error'
                if response_status_str == 'error': final_message = "CSVの処理中にエラーが発生しました。詳細はエラーリストを確認してください。"
                return Response({'status': response_status_str, 'message': final_message, 'created_count': created_count, 'updated_count': updated_count, 'errors': errors_list}, status=status_code)
            
            return Response({'status': 'success', 'message': final_message, 'created_count': created_count, 'updated_count': updated_count})

        except UnicodeDecodeError:
            return Response({'status': 'error', 'message': 'ファイルのエンコーディングが無効です。UTF-8 (BOM付き可) を使用してください。'}, status=400)
        except csv.Error as e:
            return Response({'status': 'error', 'message': f'CSV解析エラー: {e}'}, status=400)
        except Exception as e:
            import traceback
            traceback.print_exc() 
            return Response({'status': 'error', 'message': f'予期せぬサーバーエラーが発生しました: {e}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# --- ViewSets ---

class InventoryViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows inventory to be viewed or edited.
    """
    serializer_class = InventorySerializer
    pagination_class = StandardResultsSetPagination
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        part_number_query = self.request.query_params.get('part_number_query', None)
        warehouse_query = self.request.query_params.get('warehouse_query', None)
        location_query = self.request.query_params.get('location_query', None)
        hide_zero_stock_query = self.request.query_params.get('hide_zero_stock_query', 'false').lower() == 'true'

        filters = Q()
        if part_number_query:
            filters &= Q(part_number__icontains=part_number_query)
        if warehouse_query:
            filters &= Q(warehouse__icontains=warehouse_query)
        if location_query:
            filters &= Q(location__icontains=location_query)

        queryset = Inventory.objects.filter(filters)

        if hide_zero_stock_query:
            queryset = queryset.filter(
                is_active=True,
                is_allocatable=True,
                quantity__gt=F('reserved')
            )

        return queryset.order_by('part_number', 'warehouse', 'location')

    @action(detail=False, methods=['get'], url_path='by-location')
    def by_location(self, request):
        warehouse = request.query_params.get('warehouse')
        location = request.query_params.get('location')

        if not warehouse or location is None:
            return Response(
                {'success': False, 'error': '倉庫(warehouse)と棚番(location)は必須のクエリパラメータです。'},
                status=status.HTTP_400_BAD_REQUEST
            )

        inventory_items = Inventory.objects.filter(
            warehouse=warehouse,
            location=location,
            quantity__gt=0
        ).order_by('part_number')

        serializer = self.get_serializer(inventory_items, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], url_path='move')
    def move(self, request, pk=None):
        source_inventory = self.get_object()
        
        try:
            quantity_to_move = int(request.data.get('quantity_to_move'))
            target_warehouse = request.data.get('target_warehouse')
            target_location = request.data.get('target_location', '') # location can be blank
        except (TypeError, ValueError):
            return Response({'success': False, 'error': '無効なリクエストデータです。'}, status=status.HTTP_400_BAD_REQUEST)

        if not target_warehouse:
            return Response({'success': False, 'error': '移動先倉庫は必須です。'}, status=status.HTTP_400_BAD_REQUEST)
        
        if quantity_to_move <= 0:
            return Response({'success': False, 'error': '移動数量は1以上である必要があります。'}, status=status.HTTP_400_BAD_REQUEST)
            
        if quantity_to_move > source_inventory.quantity:
            return Response({'success': False, 'error': '移動数量が現在の在庫数を超えています。'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            with transaction.atomic():
                # 移動元から在庫を減らす
                source_inventory.quantity -= quantity_to_move
                source_inventory.save()

                # 移動先に在庫を追加または作成
                target_inventory, created = Inventory.objects.get_or_create(
                    part_number=source_inventory.part_number,
                    warehouse=target_warehouse,
                    location=target_location,
                    defaults={'quantity': quantity_to_move}
                )
                if not created:
                    target_inventory.quantity += quantity_to_move
                    target_inventory.save()

            return Response({'success': True, 'message': '在庫を正常に移動しました。'})

        except Exception as e:
            return Response({'success': False, 'error': f'在庫移動中にエラーが発生しました: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['post'], url_path='adjust')
    def adjust(self, request, pk=None):
        # This combines logic from the old `update_inventory_api`
        inventory = self.get_object()
        # ... implementation from `update_inventory_api` ...
        # For now, this is a placeholder. The logic is complex and needs careful integration.
        return Response({'message': 'Adjust action is not fully implemented yet.'}, status=status.HTTP_501_NOT_IMPLEMENTED)


class PurchaseOrderViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows purchase orders to be viewed or edited.
    """
    serializer_class = PurchaseOrderSerializer
    pagination_class = StandardResultsSetPagination
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        filters = Q()
        search_params_text = {
            'search_order_number': 'order_number__icontains',
            'search_shipment_number': 'shipment_number__icontains',
            'search_supplier': 'supplier__icontains',
            'search_part_number': 'part_number__icontains',
            'search_warehouse': 'warehouse__icontains',
        }
        for param, field_lookup in search_params_text.items():
            value = self.request.query_params.get(param)
            if value:
                filters &= Q(**{field_lookup: value})

        search_item_product_name = self.request.query_params.get('search_item_product_name')
        if search_item_product_name:
            filters &= (Q(item__icontains=search_item_product_name) | 
                        Q(product_name__icontains=search_item_product_name))

        search_status = self.request.query_params.get('search_status')
        if search_status:
            filters &= Q(status=search_status)

        date_filters_map = {
            'search_order_date_from': 'order_date__date__gte',
            'search_order_date_to': 'order_date__date__lte',
            'search_expected_arrival_from': 'expected_arrival__date__gte',
            'search_expected_arrival_to': 'expected_arrival__date__lte',
        }
        for param, field_lookup in date_filters_map.items():
            value = self.request.query_params.get(param)
            if value:
                filters &= Q(**{field_lookup: value})

        return PurchaseOrder.objects.filter(filters).order_by(
            F('expected_arrival').asc(nulls_last=True), 
            'order_number'
        )

    @action(detail=False, methods=['post'], url_path='process-receipt')
    def process_receipt(self, request):
        # Logic from process_purchase_receipt_api
        purchase_order_id = request.data.get('purchase_order_id')
        order_number = request.data.get('order_number')
        received_quantity = request.data.get('received_quantity')
        # ... (rest of the logic from the original function)
        # For now, this is a placeholder.
        return Response({'message': 'Process receipt action is not fully implemented yet.'}, status=status.HTTP_501_NOT_IMPLEMENTED)


class SalesOrderViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows sales orders to be viewed or edited.
    """
    serializer_class = SalesOrderSerializer
    pagination_class = StandardResultsSetPagination
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        filters = Q()
        search_order_number = self.request.query_params.get('search_order_number')
        if search_order_number:
            filters &= Q(order_number__icontains=search_order_number)

        search_item = self.request.query_params.get('search_item')
        if search_item:
            filters &= Q(item__icontains=search_item)

        search_warehouse = self.request.query_params.get('search_warehouse')
        if search_warehouse:
            filters &= Q(warehouse__icontains=search_warehouse)

        search_status = self.request.query_params.get('search_status')
        if search_status:
            filters &= Q(status=search_status)

        return SalesOrder.objects.filter(filters).order_by('expected_shipment', 'order_number')

    @action(detail=False, methods=['post'])
    def allocate(self, request):
        # Logic from allocate_inventory_for_sales_order_api
        return Response({'message': 'Allocate action is not fully implemented yet.'}, status=status.HTTP_501_NOT_IMPLEMENTED)

    @action(detail=False, methods=['post'])
    def issue(self, request):
        # Logic from process_single_sales_order_issue_api
        return Response({'message': 'Issue action is not fully implemented yet.'}, status=status.HTTP_501_NOT_IMPLEMENTED)


class StockMovementViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows stock movements to be viewed.
    """
    serializer_class = StockMovementSerializer
    pagination_class = StandardResultsSetPagination
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        filters = Q()
        text_search_params = {
            'search_part_number': 'part_number__icontains',
            'search_warehouse': 'warehouse__icontains',
            'search_reference_document': 'reference_document__icontains',
            'search_description': 'description__icontains',
            'search_operator': 'operator__username__icontains',
        }
        for param, field_lookup in text_search_params.items():
            value = self.request.query_params.get(param)
            if value:
                filters &= Q(**{field_lookup: value})

        search_movement_types = self.request.query_params.getlist('search_movement_type')
        if search_movement_types:
            filters &= Q(movement_type__in=search_movement_types)

        search_quantity = self.request.query_params.get('search_quantity')
        if search_quantity:
            try:
                filters &= Q(quantity=int(search_quantity))
            except ValueError:
                pass

        date_from = self.request.query_params.get('search_movement_date_from')
        date_to = self.request.query_params.get('search_movement_date_to')
        if date_from:
            filters &= Q(movement_date__date__gte=date_from)
        if date_to:
            filters &= Q(movement_date__date__lte=date_to)

        return StockMovement.objects.filter(filters).order_by('-movement_date', 'part_number')