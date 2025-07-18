from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination # PageNumberPagination は StandardResultsSetPagination で使用
from rest_framework.views import APIView
from .serializers import PurchaseOrderSerializer, InventorySerializer, StockMovementSerializer, AllocateInventoryForSalesOrderRequestSerializer # StockMovementSerializer をインポート
from .models import PurchaseOrder, Inventory, StockMovement, SalesOrder # SalesOrderモデルをインポート
from django.http import JsonResponse # JsonResponse をインポート
from django.db import transaction, IntegrityError # トランザクションのためにインポート # Qオブジェクトをインポートして複雑なクエリを構築
from django.db.models import Q, F # Fオブジェクトをインポート
from django.shortcuts import get_object_or_404 # オブジェクト取得のためにインポート
from django.db.models import ProtectedError # Import ProtectedError
from .serializers import SalesOrderSerializer # SalesOrderSerializer をインポート
from .forms import PurchaseOrderEntryForm # 新しいフォームをインポート
from rest_framework.views import APIView
from django.http import HttpResponse
import csv
import io
from datetime import datetime

@permission_classes([IsAuthenticated]) # 認証が必要な場合はこの行のコメントを解除してください
@api_view(['POST'])
def create_purchase_order_api(request):
    """
    新しい入庫予定を作成するAPIエンドポイント。

    リクエストボディには以下のフィールドが必要です:
    - 'order_number' (文字列): 発注番号
    - 'supplier' (整数): 仕入先のID
    - 'item' (整数): 品目のID
    - 'quantity' (整数): 発注数量
    - 'warehouse' (整数): 入庫倉庫のID
    オプションフィールド:
    - 'expected_arrival' (日時文字列): 入荷予定日 (例: "YYYY-MM-DDTHH:MM:SSZ")
    """
    serializer = PurchaseOrderSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# @login_required # ログインユーザーのみアクセス可能にする場合 (必要に応じてコメント解除)
# @api_view(['GET']) # JsonResponse を使う場合は不要
def get_stock_movement_data(request): # 関数名を変更
    """
    入出庫履歴データを取得し、JSON形式で返却するビュー (ページネーション対応)
    """
    if request.method == 'GET':
        from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

        # ページネーション設定
        # クライアントはクエリパラメータ 'page' と 'page_size' で制御できます
        page = request.GET.get('page', 1)
        page_size = request.GET.get('page_size', 25) # デフォルト件数

        try:
            page_size = int(page_size)
            # ページサイズの最小・最大を制限 (例: 1件以上、1000件以下)
            if page_size <= 0 or page_size > 1000:
                page_size = 25 # 無効な場合はデフォルトに戻す
        except (ValueError, TypeError):
            page_size = 25 # 無効な場合はデフォルトに戻す

        # StockMovement データを取得
        history_items_query = StockMovement.objects.all()

        # 詳細検索フィルタリング
        filters = Q()

        # テキストベースの検索フィールド (icontains)
        text_search_params = {
            'search_part_number': 'part_number__icontains',
            'search_warehouse': 'warehouse__icontains',
            'search_reference_document': 'reference_document__icontains',
            'search_description': 'description__icontains',
            'search_operator': 'operator__username__icontains', # 記録者ユーザー名で検索
        }
        for param, field_lookup in text_search_params.items():
            value = request.GET.get(param)
            if value:
                filters &= Q(**{field_lookup: value})

        # 移動タイプ検索 (OR条件)
        search_movement_types = request.GET.getlist('search_movement_type') # Get a list of types
        if search_movement_types: # If the list is not empty
            # Filter for records where movement_type is one of the selected types
            filters &= Q(movement_type__in=search_movement_types)

        # 数量検索 (完全一致)
        search_quantity = request.GET.get('search_quantity')
        if search_quantity:
            try:
                filters &= Q(quantity=int(search_quantity))
            except ValueError:
                pass # 無効な数値の場合は無視

        # 日付フィールド (範囲検索) - movement_date
        date_search_params = {
            'movement_date': 'movement_date',
        }
        for base_param, field_prefix in date_search_params.items(): # ループは残すが、実際には movement_date のみ
            value = request.GET.get(param)
            date_from = request.GET.get(f'search_{base_param}_from')
            date_to = request.GET.get(f'search_{base_param}_to')
            if date_from:
                filters &= Q(**{f'{field_prefix}__date__gte': date_from})
            if date_to:
                filters &= Q(**{f'{field_prefix}__date__lte': date_to})
        

        if filters: # filtersがQ()のまま（空）でない場合のみ適用
            history_items_query = history_items_query.filter(filters)

        # デフォルトのソート順を移動日時の降順に変更
        history_items = history_items_query.order_by('-movement_date', 'part_number')

        paginator = Paginator(history_items, page_size)

        try:
            history_items_page = paginator.page(page)
        except PageNotAnInteger:
            history_items_page = paginator.page(1) # ページ番号が整数でない場合は1ページ目
        except EmptyPage:
            history_items_page = paginator.page(paginator.num_pages) # ページが空の場合は最終ページ

        # StockMovementSerializer を使用してデータをシリアライズ
        serializer = StockMovementSerializer(history_items_page, many=True)
        data = serializer.data

        # ページネーション情報をレスポンスに含める
        response_data = {
            'count': paginator.count, # 総件数
            'num_pages': paginator.num_pages, # 総ページ数
            'current_page': history_items_page.number, # 現在のページ番号
            'next': history_items_page.next_page_number() if history_items_page.has_next() else None, # 次のページ番号 (なければ None)
            'previous': history_items_page.previous_page_number() if history_items_page.has_previous() else None, # 前のページ番号 (なければ None)
            'results': data # ページングされたデータ
        }
        return JsonResponse(response_data, safe=False)
    else:
        return JsonResponse({'error': 'Invalid request method'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)


@api_view(['POST'])
# @permission_classes([IsAuthenticated]) # 認証が必要な場合はこの行のコメントを解除してください
def process_purchase_receipt_api(request):
    """
    入庫処理を実行するAPIエンドポイント。

    指定された入庫予定に対して、実際の入庫数量を記録し、在庫を更新します。

    リクエストボディには以下のフィールドが必要です:
    - 'purchase_order_id' (UUID文字列) または 'order_number' (文字列): 入庫処理を行う入庫予定のIDまたは発注番号。どちらか一方は必須です。'purchase_order_id' が優先されます。
    - 'received_quantity' (整数): 今回入庫する数量
    - 'location' (文字列, オプション): 実際に入庫した倉庫内の場所
    """
    purchase_order_id = request.data.get('purchase_order_id')
    order_number = request.data.get('order_number')
    received_quantity = request.data.get('received_quantity')
    requested_warehouse_str = request.data.get('warehouse') # Warehouse from request
    requested_location_str = request.data.get('location')   # Location from request, can be None or empty string

    if (not purchase_order_id and not order_number) or received_quantity is None:
        return Response(
            {"error": "purchase_order_id または order_number のいずれかと、received_quantity は必須です。"},
            # {"error": "Either purchase_order_id or order_number, and received_quantity are required."},
            status=status.HTTP_400_BAD_REQUEST
        )


    try:
        # received_quantity が正の整数であることを検証
        received_quantity = int(received_quantity)
        if received_quantity <= 0:
            return Response(
                {"error": "received_quantity は正の整数である必要があります。"},
                status=status.HTTP_400_BAD_REQUEST
            )
    except (ValueError, TypeError):
        return Response(
            {"error": "received_quantity は有効な整数である必要があります。"},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        # データベース操作の原子性を保証するためにトランザクションを使用
        with transaction.atomic():
            # 1. 入庫予定オブジェクトを取得 (purchase_order_id があれば優先、なければ order_number で検索)
            if purchase_order_id:
                purchase_order = get_object_or_404(PurchaseOrder, id=purchase_order_id)
            elif order_number:
                purchase_order = get_object_or_404(PurchaseOrder, order_number=order_number)
            else: # このケースは上記の必須チェックでカバーされるはずだが念のため
                return Response({"error": "内部エラー: IDまたは発注番号が特定できませんでした。"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            # POが既に完了またはキャンセルされていないかチェック
            if purchase_order.status == 'received':
                 return Response(
                    {"error": f"入庫予定 {purchase_order.order_number} は既に入庫完了しています。"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            if purchase_order.status == 'canceled':
                 return Response(
                    {"error": f"入庫予定 {purchase_order.order_number} はキャンセルされています。"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # 残りの入庫予定数量を計算
            remaining_to_receive = purchase_order.quantity - purchase_order.received_quantity

            # 今回の入庫数量が残り数量を超える場合の処理 (ビジネスロジックによる)
            # 超過分を許可しない場合はエラーを返す
            if received_quantity > remaining_to_receive:
                 # エラーを返す場合:
                 # return Response(
                 #    {"error": f"入庫数量 ({received_quantity}) が入庫予定の残り数量 ({remaining_to_receive}) を超えています。"},
                 #    status=status.HTTP_400_BAD_REQUEST
                 # )
                 # 残り数量のみを処理する場合:
                 print(f"警告: 入庫数量 ({received_quantity}) が入庫予定の残り数量 ({remaining_to_receive}) を超えています。残り数量 ({remaining_to_receive}) のみ処理します。")
                 actual_received_quantity = remaining_to_receive
                 if actual_received_quantity <= 0: # 残り数量が0以下の場合は処理しない
                      return Response(
                         {"error": f"入庫予定 {purchase_order.order_number} には入庫する残り数量がありません。"},
                         status=status.HTTP_400_BAD_REQUEST
                     )
            else:
                actual_received_quantity = received_quantity

            # 2. POの received_quantity を更新
            purchase_order.received_quantity += actual_received_quantity

            # 3. (変更) StockMovement には PurchaseOrder の item 文字列を直接使用するため、
            #    Item オブジェクトの検索は不要になりました。
            # Warehouse オブジェクトの検索は、Inventory が文字列を格納するようになり、
            # StockMovement が倉庫情報を持たないため、不要になりました。

            # 実際に入庫する倉庫を決定 (リクエストで指定があればそれを優先、なければPOの倉庫)
            # If requested_warehouse_str is provided (not None and not empty string), use it. Otherwise, use PO's warehouse.
            target_warehouse = requested_warehouse_str if requested_warehouse_str is not None and requested_warehouse_str.strip() != "" else purchase_order.warehouse
            if not target_warehouse: # POにも設定がなく、リクエストからも来なかった場合
                return Response(
                    {"error": "入庫先の倉庫情報が不明です。発注情報に倉庫を設定するか、処理時に指定してください。"},
                    # {"error": "Warehouse information for receipt is unknown. Set it in the PO or specify during processing."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # 実際に入庫する棚番を決定
            # If requested_location_str is provided (not None), use it. Otherwise, use PO's location (which can be None or empty).
            # An empty string from request means "clear location" or "no specific location".
            target_location = requested_location_str if requested_location_str is not None else purchase_order.location
            target_location_str = target_location if target_location is not None else '' # Normalize for get_or_create

            # 4. 対応する Inventory レコードを検索または新規作成し、数量を更新
            #    Inventory の item と warehouse は PurchaseOrder からの文字列を直接使用
            inventory_item, created = Inventory.objects.get_or_create(
                part_number=purchase_order.part_number, # PurchaseOrder の part_number を使用
                warehouse=target_warehouse, # 実際に入庫する倉庫を使用
                location=target_location_str, # Use determined target location
                defaults={'quantity': 0}    # Location is now part of the query criteria
            )
            inventory_item.quantity += actual_received_quantity
 
            # 既存レコードの場合で、かつリクエストに location が指定されていれば更新
            # また、もしget_or_createで取得したInventoryのwarehouseがtarget_warehouseと異なる場合(通常はありえないが)、更新する
            inventory_item.warehouse = target_warehouse # 念のため、取得/作成された在庫の倉庫をターゲットに合わせる
            # inventory_item.location is already set by get_or_create
            # Location is part of the key, so it's already correct for the fetched/created item.
            # If location_str was different from item's original location, a new record would be made or a different one fetched.
            inventory_item.save()

            # 5. StockMovement レコードを作成 (入庫履歴)
            StockMovement.objects.create(
                part_number=purchase_order.part_number, # PurchaseOrder の part_number を使用
                warehouse=target_warehouse, # 実際に入庫した倉庫
                movement_type='incoming',
                quantity=actual_received_quantity,
                description=f"PO {purchase_order.order_number} による入庫 (倉庫: {target_warehouse}" + (f", 場所: {target_location_str})" if target_location_str else ")"),
                operator=request.user if request.user.is_authenticated else None,
            )

            # 6. 入庫完了した場合、POのステータスを更新
            if purchase_order.received_quantity >= purchase_order.quantity:
                purchase_order.status = 'received'

            purchase_order.save()

            # 7. 更新されたPOデータをレスポンスとして返却
            serializer = PurchaseOrderSerializer(purchase_order)
            return Response(serializer.data, status=status.HTTP_200_OK)

    except PurchaseOrder.DoesNotExist:
        return Response(
            {"error": f"指定された入庫予定 (ID: {purchase_order_id}, 発注番号: {order_number}) が見つかりませんでした。"},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        # その他の予期しないエラーをキャッチ
        print(f"入庫処理中にエラーが発生しました: {e}")
        return Response(
            {"error": "入庫処理中に内部エラーが発生しました。"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


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


# @login_required # ログインユーザーのみアクセス可能にする場合 (必要に応じてコメント解除)
# @permission_classes([IsAuthenticated]) # 必要に応じて認証を追加
@api_view(['GET']) # DRFの Response を使うため @api_view デコレータを使用
def get_inventory_data(request):
    """
    在庫情報を取得し、JSON形式で返却するビュー (DRFページネーション対応)
    """
    if request.method == 'GET':
        # DRFページネーションを適用
        paginator = StandardResultsSetPagination()

        # フィルタリングのためのクエリパラメータを取得
        part_number_query = request.query_params.get('part_number_query', None)
        warehouse_query = request.query_params.get('warehouse_query', None)
        location_query = request.query_params.get('location_query', None)
        hide_zero_stock_query = request.query_params.get('hide_zero_stock_query', 'false').lower() == 'true'

        filters = Q()
        if part_number_query:
            filters &= Q(part_number__icontains=part_number_query)
        if warehouse_query:
            filters &= Q(warehouse__icontains=warehouse_query)
        if location_query:
            filters &= Q(location__icontains=location_query)

        inventories_qs = Inventory.objects.filter(filters)

        if hide_zero_stock_query:
            # 利用可能在庫が0より大きいものをフィルタリング
            # available_quantity のロジック: is_active=True, is_allocatable=True, quantity > reserved
            inventories_qs = inventories_qs.filter(
                is_active=True,
                is_allocatable=True,
                quantity__gt=F('reserved')
            )

        paginated_inventories = paginator.paginate_queryset(inventories_qs.order_by('part_number', 'warehouse', 'location'), request)

        # ページングされたクエリセットをシリアライズ
        serializer = InventorySerializer(paginated_inventories, many=True)
        # DRF標準のページネーション形式でレスポンスを構築して返却
        return paginator.get_paginated_response(serializer.data)
    else:
        # DRFの Response を使う場合、エラーレスポンスも Response で統一するのが良い
        return Response({'error': 'Invalid request method'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)


@api_view(['POST'])
# @permission_classes([IsAuthenticated]) # Uncomment if authentication is required
def allocate_inventory_for_sales_order_api(request):
    """
    Allocates inventory for a sales order.
    This endpoint reserves quantities for specified part numbers in given warehouses.
    The operation is atomic: all allocations succeed, or none are applied.

    Request Body:
    {
      "sales_order_reference": "SO12345",
      "allocations": [
        {"part_number": "PN001", "warehouse": "WH-A", "quantity_to_reserve": 10},
        {"part_number": "PN002", "warehouse": "WH-B", "quantity_to_reserve": 5}
      ]
    }
    """
    serializer = AllocateInventoryForSalesOrderRequestSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    validated_data = serializer.validated_data
    sales_order_ref = validated_data['sales_order_reference'] # Renamed for clarity and consistency
    allocations_data = validated_data['allocations'] # This will be a list of allocation items

    from .models import SalesOrder, Inventory # Import SalesOrder and Inventory models

    processed_allocations_summary = []

    try:
        with transaction.atomic():
            # Iterate over the list of allocations provided in the request
            for alloc_item_data in allocations_data:
                part_number = alloc_item_data['part_number']
                warehouse = alloc_item_data['warehouse']
                quantity_to_reserve = alloc_item_data['quantity_to_reserve']

                try:
                    # Lock the inventory row for the duration of the transaction
                    inventory_item = Inventory.objects.select_for_update().get(
                        part_number=part_number,
                        warehouse=warehouse
                    )
                except Inventory.DoesNotExist:
                    raise ValueError(f"Inventory record not found for part '{part_number}' in warehouse '{warehouse}'.")

                if not inventory_item.is_active or not inventory_item.is_allocatable:
                    raise ValueError(f"Inventory for part '{part_number}' in warehouse '{warehouse}' is not active or not allocatable.")

                if inventory_item.available_quantity < quantity_to_reserve:
                    raise ValueError(
                        f"Insufficient available stock for part '{part_number}' in warehouse '{warehouse}'. "
                        f"Required: {quantity_to_reserve}, Available: {inventory_item.available_quantity}"
                    )

                inventory_item.reserved += quantity_to_reserve
                inventory_item.save()

                # Create SalesOrder if it doesn't exist for this sales_order_ref,
                # or verify consistency if it does.
                # The sales_order_ref is assumed to uniquely identify the sales order line.
                sales_order, so_created = SalesOrder.objects.get_or_create(
                    order_number=sales_order_ref,
                    defaults={
                        'item': part_number,
                        'quantity': quantity_to_reserve, # SalesOrder.quantity set by the first reservation's amount
                        'warehouse': warehouse,
                        'status': 'pending'
                    }
                )

                if not so_created:
                    # SalesOrder already existed. Verify consistency with the current allocation.
                    mismatch = False
                    if sales_order.item != part_number:
                        mismatch = True
                    # Compare warehouse, handling None carefully
                    if warehouse is None and sales_order.warehouse is not None:
                        mismatch = True
                    elif warehouse is not None and sales_order.warehouse != warehouse:
                        mismatch = True
                    
                    if mismatch:
                        raise ValueError(
                            f"Sales Order '{sales_order_ref}' (ID: {sales_order.id}) already exists but with conflicting item/warehouse. "
                            f"Existing: item='{sales_order.item}', warehouse='{sales_order.warehouse}'. "
                            f"Current allocation request: item='{part_number}', warehouse='{warehouse}'."
                        )

                processed_allocations_summary.append({
                    "part_number": part_number,
                    "warehouse": warehouse,
                    "reserved_quantity": quantity_to_reserve,
                    "sales_order_created": so_created,
                    "new_total_reserved": inventory_item.reserved,
                    "new_available_quantity": inventory_item.available_quantity  # Property will recalculate
                })
            
            return Response({
                "message": "Inventory allocated successfully.",
                "sales_order_reference": sales_order_ref,
                "sales_order_id": sales_order.id, # Include SalesOrder ID in response
                "allocations_summary": processed_allocations_summary
            }, status=status.HTTP_200_OK)

    except ValueError as e: # Handles custom errors like DoesNotExist, not active/allocatable, insufficient stock
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e: # Catch-all for other unexpected errors
        # It's good practice to log the exception 'e' here for debugging purposes
        return Response({"error": "An unexpected error occurred during allocation.", "detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
# @permission_classes([IsAuthenticated]) # Uncomment if authentication is required
def process_single_sales_order_issue_api(request):
    """
    Processes the issuing of items for a single sales order based on provided quantity.

    Request Body (JSON):
    {
      "order_id": "uuid_of_sales_order",
      "quantity_to_ship": 10
    }
    """
    try:
        order_id = request.data.get('order_id')
        quantity_to_ship_str = request.data.get('quantity_to_ship')

        if not order_id or quantity_to_ship_str is None:
            return JsonResponse({'success': False, 'error': 'order_id と quantity_to_ship は必須です。'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            quantity_to_ship = int(quantity_to_ship_str)
            if quantity_to_ship <= 0:
                return JsonResponse({'success': False, 'error': '出庫数量は0より大きい必要があります。'}, status=status.HTTP_400_BAD_REQUEST)
        except ValueError:
            return JsonResponse({'success': False, 'error': '出庫数量は有効な数値である必要があります。'}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            sales_order = get_object_or_404(SalesOrder.objects.select_for_update(), id=order_id)

            if sales_order.status == 'shipped':
                return JsonResponse({'success': False, 'error': f"受注 {sales_order.order_number} は既に出庫済みです。"}, status=status.HTTP_400_BAD_REQUEST)
            if sales_order.status == 'canceled':
                return JsonResponse({'success': False, 'error': f"受注 {sales_order.order_number} はキャンセルされています。"}, status=status.HTTP_400_BAD_REQUEST)

            if not sales_order.item or not sales_order.warehouse:
                return JsonResponse({'success': False, 'error': f"受注 {sales_order.order_number} に品目または倉庫が指定されていません。"}, status=status.HTTP_400_BAD_REQUEST)

            if quantity_to_ship > sales_order.remaining_quantity:
                return JsonResponse({
                    'success': False,
                    'error': f"出庫数量 ({quantity_to_ship}) が残数量 ({sales_order.remaining_quantity}) を超えています。"
                }, status=status.HTTP_400_BAD_REQUEST)

            try:
                inventory_item = Inventory.objects.select_for_update().get(
                    part_number=sales_order.item,
                    warehouse=sales_order.warehouse
                )
            except Inventory.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'error': f"在庫記録が見つかりません: 品目 {sales_order.item}、倉庫 {sales_order.warehouse} (受注: {sales_order.order_number})"
                }, status=status.HTTP_404_NOT_FOUND)

            if not inventory_item.is_active:
                return JsonResponse({
                    'success': False,
                    'error': f"在庫品目 {sales_order.item} (倉庫: {sales_order.warehouse}) は有効ではありません。"
                }, status=status.HTTP_400_BAD_REQUEST)

            if inventory_item.quantity < quantity_to_ship:
                return JsonResponse({
                    'success': False,
                    'error': f"在庫不足: {sales_order.item} (倉庫: {sales_order.warehouse})。実在庫: {inventory_item.quantity}, 要求: {quantity_to_ship}。"
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Optional: Check reserved quantity consistency, though primary check is on available quantity.
            if inventory_item.reserved < quantity_to_ship:
                 # This might be a warning or an error depending on business logic.
                 # For now, we proceed if total quantity is sufficient, and consume reservation.
                 print(f"Warning for SO {sales_order.order_number}: Reserved quantity ({inventory_item.reserved}) is less than shipping quantity ({quantity_to_ship}). Shipping based on total available stock.")


            # Update Inventory
            inventory_item.quantity -= quantity_to_ship
            inventory_item.reserved -= min(inventory_item.reserved, quantity_to_ship) # Consume reservation
            inventory_item.save()

            # Update SalesOrder
            sales_order.shipped_quantity += quantity_to_ship
            if sales_order.remaining_quantity <= 0:
                sales_order.status = 'shipped'
            sales_order.save()

            # Create StockMovement record
            StockMovement.objects.create(
                part_number=sales_order.item,
                movement_type='outgoing',
                quantity=quantity_to_ship,
                description=f"SO {sales_order.order_number} による出庫 (倉庫: {sales_order.warehouse})",
                operator=request.user if request.user.is_authenticated else None,
            )

            return JsonResponse({'success': True, 'message': f"受注 {sales_order.order_number} から {quantity_to_ship} 個の {sales_order.item} を出庫しました。"})

    except SalesOrder.DoesNotExist:
        return JsonResponse({'success': False, 'error': f"受注ID {order_id} が見つかりません。"}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        # Log the exception e for server-side debugging
        print(f"Error processing single sales order issue: {e}")
        return JsonResponse({'success': False, 'error': f"出庫処理中に予期せぬエラーが発生しました: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
# @permission_classes([IsAuthenticated]) # Ensure user is authenticated
def update_inventory_api(request):
    """
    Updates the quantity of a specific inventory item and records the movement.

    Request Body (JSON):
    {
      "inventory_id": "uuid_of_inventory_item",
      "quantity": 100,
      "warehouse": "new_warehouse_name", // Optional, if not provided or empty, current warehouse is used
      "location": "new_location_name"    // Optional, if not provided, current location is used. Empty string clears location.
    }
    """
    try:
        inventory_id = request.data.get('inventory_id')
        new_quantity_str = request.data.get('quantity')
        
        # New fields for warehouse and location
        requested_warehouse_str = request.data.get('warehouse') 
        requested_location_str = request.data.get('location', '')   # Normalize None to empty string for consistency

        if not inventory_id or new_quantity_str is None: # Quantity is still mandatory
            return Response({'success': False, 'error': 'inventory_id と quantity は必須です。'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            new_target_quantity = int(new_quantity_str)
            if new_target_quantity < 0:
                return Response({'success': False, 'error': '数量は0以上である必要があります。'}, status=status.HTTP_400_BAD_REQUEST)
        except ValueError:
            return Response({'success': False, 'error': '数量は有効な数値である必要があります。'}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            source_inventory = get_object_or_404(Inventory.objects.select_for_update(), id=inventory_id)
            
            original_part_number = source_inventory.part_number
            original_warehouse = source_inventory.warehouse
            original_location = source_inventory.location
            original_quantity = source_inventory.quantity

            # Determine target warehouse: if not provided or empty, use original.
            target_warehouse = requested_warehouse_str if requested_warehouse_str is not None and requested_warehouse_str.strip() != "" else original_warehouse
            # Determine target location: if 'location' key was present in request.data, use its value (even if empty string).
            # Otherwise (key not present), use original_location.
            target_location = requested_location_str if request.data.get('location') is not None else original_location
            
            final_report_item = source_inventory # Default for serializer response
            message_parts = []

            # Scenario 1: Warehouse AND Location are NOT changing from the source_inventory's perspective
            # This means we are updating the quantity of the existing inventory record.
            if target_warehouse == original_warehouse and target_location == original_location:
                location_changed = (target_location != original_location)
                quantity_changed = (new_target_quantity != original_quantity)

                if not quantity_changed: # Only quantity can change here, location is same
                    return Response({'success': True, 'message': '在庫情報に変更はありませんでした。', 'data': InventorySerializer(source_inventory).data}, status=status.HTTP_200_OK)

                if location_changed:
                    message_parts.append(f"棚番: '{original_location or '-'}'->'{target_location or '-'}'")
                if quantity_changed:
                    message_parts.append(f"数量: {original_quantity}->{new_target_quantity}")
                
                source_inventory.location = target_location # No change, but set for clarity
                source_inventory.quantity = new_target_quantity # Update quantity
                source_inventory.save()

                if quantity_changed and abs(new_target_quantity - original_quantity) > 0 : # Log StockMovement if quantity changed
                    StockMovement.objects.create(
                        part_number=original_part_number,
                        warehouse=original_warehouse,
                        movement_type='adjustment',
                        quantity=abs(new_target_quantity - original_quantity),
                        description=f"在庫修正 ({original_warehouse}): {', '.join(message_parts)}",
                        operator=request.user if request.user.is_authenticated else None
                    )
                final_report_item = source_inventory
                message = f"在庫情報を更新しました: {', '.join(message_parts)}"

            else: # Scenario 2: Warehouse OR Location (or both) ARE changing
                # This is treated as a move of the *entire* original_quantity from the source_inventory's
                # (part_number, original_warehouse, original_location) slot to a new slot defined by
                # (part_number, target_warehouse, target_location).
                # Then, the quantity at the new slot is adjusted to new_target_quantity.

                message_parts.append(f"移動: {original_part_number} [{original_warehouse}/{original_location or '-'}] -> [{target_warehouse}/{target_location or '-'}]")
                message_parts.append(f"旧数量: {original_quantity}, 新最終数量: {new_target_quantity}")

                # Step A: Outgoing from source_inventory (original slot)
                if original_quantity > 0: # Only create movement if there was stock
                    StockMovement.objects.create(
                        part_number=original_part_number,
                        warehouse=original_warehouse,
                        movement_type='outgoing', 
                        quantity=original_quantity,
                        description=f"在庫修正(移動出庫): {original_quantity}個 @ {original_warehouse}/{original_location or '-'} to {target_warehouse}/{target_location or '-'}",
                        operator=request.user if request.user.is_authenticated else None
                    )
                
                source_inventory.quantity = 0 
                source_inventory.save() # Save the source with 0 quantity

                # Step B: Incoming to target_inventory_item (new slot)
                target_inventory_item, created = Inventory.objects.get_or_create(
                    part_number=original_part_number,
                    warehouse=target_warehouse,
                    location=target_location, # target_location is part of the key
                    defaults={'quantity': 0} 
                )
                
                quantity_at_target_before_this_move = target_inventory_item.quantity
                target_inventory_item.quantity += original_quantity # Add the moved quantity

                if original_quantity > 0: # Log incoming movement if quantity was moved
                    StockMovement.objects.create(
                        part_number=original_part_number,
                        warehouse=target_warehouse,
                        movement_type='incoming', 
                        quantity=original_quantity,
                        description=f"在庫修正(移動入庫): {original_quantity}個 @ {target_warehouse}/{target_location or '-'} from {original_warehouse}/{original_location or '-'}",
                        operator=request.user if request.user.is_authenticated else None
                    )
                
                # Step C: Adjust quantity at target_inventory_item to new_target_quantity
                # Current quantity at target is (quantity_at_target_before_this_move + original_quantity)
                # We want it to be new_target_quantity.
                # So, the adjustment needed is new_target_quantity - (quantity_at_target_before_this_move + original_quantity)
                
                current_total_at_target = target_inventory_item.quantity # This is after adding original_quantity
                adjustment_diff = new_target_quantity - current_total_at_target

                target_inventory_item.quantity = new_target_quantity # Set to final desired quantity
                # target_inventory_item.location is already set correctly by get_or_create
                target_inventory_item.save()

                if adjustment_diff != 0: # Log adjustment if needed
                     StockMovement.objects.create(
                        part_number=original_part_number,
                        warehouse=target_warehouse,
                        movement_type='adjustment',
                        quantity=abs(adjustment_diff),
                        description=f"在庫修正(移動後調整)@{target_warehouse}/{target_location or '-'}: {current_total_at_target} -> {new_target_quantity} (差分 {adjustment_diff})",
                        operator=request.user if request.user.is_authenticated else None
                    )
                final_report_item = target_inventory_item
                message = f"在庫情報を更新しました: {', '.join(message_parts)}"
            
            return Response({'success': True, 'message': message, 'data': InventorySerializer(final_report_item).data}, status=status.HTTP_200_OK)

    except Inventory.DoesNotExist:
        return Response({'success': False, 'error': f"在庫ID {inventory_id} が見つかりません。"}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        print(f"Error updating inventory: {e}") # Log for server-side debugging
        import traceback
        traceback.print_exc()
        return Response({'success': False, 'error': f"在庫更新中に予期せぬエラーが発生しました: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
# @permission_classes([IsAuthenticated]) # Uncomment if authentication is required
def move_inventory_api(request):
    """
    Moves a specified quantity of an inventory item from a source to a target warehouse/location.

    Request Body (JSON):
    {
      "source_inventory_id": "uuid_of_source_inventory_item",
      "quantity_to_move": 50,
      "target_warehouse": "target_warehouse_name",
      "target_location": "target_location_name" // Optional
    }
    """
    try:
        source_inventory_id = request.data.get('source_inventory_id')
        quantity_to_move_str = request.data.get('quantity_to_move')
        target_warehouse_str = request.data.get('target_warehouse')
        target_location_str = request.data.get('target_location', '') # Default to empty string if not provided

        if not all([source_inventory_id, quantity_to_move_str, target_warehouse_str]):
            return Response({'success': False, 'error': 'source_inventory_id, quantity_to_move, target_warehouse は必須です。'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            quantity_to_move = int(quantity_to_move_str)
            if quantity_to_move <= 0:
                return Response({'success': False, 'error': '移動数量は0より大きい正の整数である必要があります。'}, status=status.HTTP_400_BAD_REQUEST)
        except ValueError:
            return Response({'success': False, 'error': '移動数量は有効な数値である必要があります。'}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            source_inventory = get_object_or_404(Inventory.objects.select_for_update(), id=source_inventory_id)

            if source_inventory.warehouse == target_warehouse_str and source_inventory.location == target_location_str:
                return Response({'success': False, 'error': '移動元と移動先が同じです。倉庫または棚番を変更してください。'}, status=status.HTTP_400_BAD_REQUEST)

            if source_inventory.quantity < quantity_to_move:
                return Response({'success': False, 'error': f"移動元の在庫数量 ({source_inventory.quantity}) が不足しています。移動しようとしている数量: {quantity_to_move}"}, status=status.HTTP_400_BAD_REQUEST)

            original_part_number = source_inventory.part_number
            original_source_warehouse = source_inventory.warehouse
            original_source_location = source_inventory.location

            # Decrease quantity from source
            source_inventory.quantity -= quantity_to_move
            source_inventory.save()

            StockMovement.objects.create(
                part_number=original_part_number,
                warehouse=original_source_warehouse,
                movement_type='outgoing',
                quantity=quantity_to_move,
                description=f"在庫移動(出庫): {quantity_to_move}個を {original_source_warehouse}/{original_source_location or '-'} から {target_warehouse_str}/{target_location_str or '-'} へ",
                operator=request.user if request.user.is_authenticated else None
            )

            # Get or create target inventory and update it
            target_inventory, created = Inventory.objects.get_or_create(
                part_number=original_part_number,
                warehouse=target_warehouse_str,
                location=target_location_str, # Add location to the query criteria
                defaults={'quantity': 0}      # Location is now part of the key
            )
            target_inventory.quantity += quantity_to_move
            # target_inventory.location is already correct due to get_or_create
            target_inventory.save()

            StockMovement.objects.create(
                part_number=original_part_number,
                warehouse=target_warehouse_str,
                movement_type='incoming',
                quantity=quantity_to_move,
                description=f"在庫移動(入庫): {quantity_to_move}個を {target_warehouse_str}/{target_location_str or '-'} へ (元: {original_source_warehouse}/{original_source_location or '-'})",
                operator=request.user if request.user.is_authenticated else None
            )

            return Response({'success': True, 'message': f"{original_part_number} を {quantity_to_move} 個、{original_source_warehouse} から {target_warehouse_str} へ移動しました。"}, status=status.HTTP_200_OK)

    except Inventory.DoesNotExist:
        return Response({'success': False, 'error': f"移動元の在庫ID {source_inventory_id} が見つかりません。"}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        print(f"Error moving inventory: {e}")
        import traceback
        traceback.print_exc()
        return Response({'success': False, 'error': f"在庫移動中に予期せぬエラーが発生しました: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
# @permission_classes([IsAuthenticated]) # Uncomment if authentication is required
def get_inventory_by_location_api(request):
    """
    Retrieves a list of inventory items at a specific warehouse and location.
    Used by the mobile location transfer screen to find items to move.

    Query Parameters:
    - warehouse (string, required): The warehouse code.
    - location (string, required): The location code. Can be an empty string.
    """
    warehouse = request.query_params.get('warehouse')
    location = request.query_params.get('location') # location can be None if not provided

    if not warehouse or location is None:
        return Response(
            {'success': False, 'error': '倉庫(warehouse)と棚番(location)は必須のクエリパラメータです。'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        # Find inventory items with quantity greater than 0 at the specified location
        inventory_items = Inventory.objects.filter(
            warehouse=warehouse,
            location=location,
            quantity__gt=0
        ).order_by('part_number')

        serializer = InventorySerializer(inventory_items, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    except Exception as e:
        print(f"Error in get_inventory_by_location_api: {e}")
        return Response(
            {'success': False, 'error': f"在庫の検索中に予期せぬエラーが発生しました: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
# @permission_classes([IsAuthenticated]) # Uncomment if authentication is required
def get_inventory_by_location_api(request):
    """
    Retrieves a list of inventory items at a specific warehouse and location.
    Used by the mobile location transfer screen to find items to move.

    Query Parameters:
    - warehouse (string, required): The warehouse code.
    - location (string, required): The location code. Can be an empty string.
    """
    warehouse = request.query_params.get('warehouse')
    location = request.query_params.get('location') # location can be None if not provided

    if not warehouse or location is None:
        return Response(
            {'success': False, 'error': '倉庫(warehouse)と棚番(location)は必須のクエリパラメータです。'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        # Find inventory items with quantity greater than 0 at the specified location
        inventory_items = Inventory.objects.filter(
            warehouse=warehouse,
            location=location,
            quantity__gt=0
        ).order_by('part_number')

        serializer = InventorySerializer(inventory_items, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    except Exception as e:
        print(f"Error in get_inventory_by_location_api: {e}")
        return Response(
            {'success': False, 'error': f"在庫の検索中に予期せぬエラーが発生しました: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['POST'])
# @permission_classes([IsAuthenticated]) # Uncomment if authentication is required
def location_transfer_api(request):
    """
    Moves a specified quantity of an inventory item from a source location to a target location
    within the same warehouse. Designed for mobile/scanner-based workflows.

    Request Body (JSON):
    {
      "part_number": "PART-001",
      "quantity_to_move": 10,
      "warehouse": "MAIN-WH",
      "source_location": "A-01-01",
      "target_location": "B-02-01"
    }
    """
    try:
        part_number = request.data.get('part_number')
        quantity_to_move_str = request.data.get('quantity_to_move')
        warehouse = request.data.get('warehouse')
        source_location = request.data.get('source_location', '') # Default to empty string
        target_location = request.data.get('target_location', '') # Default to empty string

        if not all([part_number, quantity_to_move_str, warehouse]):
            return Response({'success': False, 'error': '品番、移動数量、倉庫は必須です。'}, status=status.HTTP_400_BAD_REQUEST)

        if source_location == target_location:
            return Response({'success': False, 'error': '移動元と移動先の棚番が同じです。'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            quantity_to_move = int(quantity_to_move_str)
            if quantity_to_move <= 0:
                return Response({'success': False, 'error': '移動数量は0より大きい正の整数である必要があります。'}, status=status.HTTP_400_BAD_REQUEST)
        except ValueError:
            return Response({'success': False, 'error': '移動数量は有効な数値である必要があります。'}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            # Find source inventory
            try:
                source_inventory = Inventory.objects.select_for_update().get(
                    part_number=part_number,
                    warehouse=warehouse,
                    location=source_location
                )
            except Inventory.DoesNotExist:
                return Response({'success': False, 'error': f"移動元の在庫が見つかりません: 品番 {part_number}, 倉庫 {warehouse}, 棚番 '{source_location}'"}, status=status.HTTP_404_NOT_FOUND)

            if source_inventory.quantity < quantity_to_move:
                return Response({'success': False, 'error': f"移動元の在庫数量 ({source_inventory.quantity}) が不足しています。移動しようとしている数量: {quantity_to_move}"}, status=status.HTTP_400_BAD_REQUEST)

            # Decrease quantity from source and create outgoing movement
            source_inventory.quantity -= quantity_to_move
            source_inventory.save()

            StockMovement.objects.create(
                part_number=part_number, warehouse=warehouse, movement_type='outgoing', quantity=quantity_to_move,
                description=f"棚番移動(出庫): {quantity_to_move}個を {warehouse}/{source_location or '-'} から {warehouse}/{target_location or '-'} へ",
                operator=request.user if request.user.is_authenticated else None
            )

            # Get or create target inventory, update quantity, and create incoming movement
            target_inventory, _ = Inventory.objects.get_or_create(
                part_number=part_number, warehouse=warehouse, location=target_location, defaults={'quantity': 0}
            )
            target_inventory.quantity += quantity_to_move
            target_inventory.save()

            StockMovement.objects.create(
                part_number=part_number, warehouse=warehouse, movement_type='incoming', quantity=quantity_to_move,
                description=f"棚番移動(入庫): {quantity_to_move}個を {warehouse}/{target_location or '-'} へ (元: {warehouse}/{source_location or '-'})",
                operator=request.user if request.user.is_authenticated else None
            )

            return Response({'success': True, 'message': f"{part_number} を {quantity_to_move} 個、棚番 '{source_location or 'N/A'}' から '{target_location or 'N/A'}' へ移動しました。"}, status=status.HTTP_200_OK)

    except Exception as e:
        print(f"Error during location transfer: {e}")
        return Response({'success': False, 'error': f"棚番移動中に予期せぬエラーが発生しました: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
# @permission_classes([IsAuthenticated]) # Uncomment if authentication is required
def get_purchase_orders_api(request):
    """
    Retrieves a paginated list of purchase orders with filtering capabilities.
    This endpoint is used by the purchase receipt page.
    """
    paginator = StandardResultsSetPagination()
    
    filters = Q()

    # Text-based search fields
    search_params_text = {
        'search_order_number': 'order_number__icontains',
        'search_shipment_number': 'shipment_number__icontains',
        'search_supplier': 'supplier__icontains', # Assuming supplier is stored as CharField
        'search_part_number': 'part_number__icontains',
        'search_warehouse': 'warehouse__icontains', # Assuming warehouse is stored as CharField
    }
    for param, field_lookup in search_params_text.items():
        value = request.query_params.get(param)
        if value:
            filters &= Q(**{field_lookup: value})

    # Special search for item/product name
    search_item_product_name = request.query_params.get('search_item_product_name')
    if search_item_product_name:
        filters &= (Q(item__icontains=search_item_product_name) | 
                    Q(product_name__icontains=search_item_product_name))

    # Status filter (exact match)
    search_status = request.query_params.get('search_status')
    if search_status:
        filters &= Q(status=search_status)

    # Date range filters
    date_filters_map = {
        'search_order_date_from': 'order_date__date__gte',
        'search_order_date_to': 'order_date__date__lte',
        'search_expected_arrival_from': 'expected_arrival__date__gte',
        'search_expected_arrival_to': 'expected_arrival__date__lte',
    }
    for param, field_lookup in date_filters_map.items():
        value = request.query_params.get(param)
        if value:
            filters &= Q(**{field_lookup: value})

    # order_by の指定: expected_arrival の昇順、次に order_number の昇順
    # expected_arrival が NULL の場合は最後に表示されるように調整 (Fオブジェクトとasc/desc(nulls_last=True)を使用)
    # Django 3.2以降では F().asc(nulls_last=True) や F().desc(nulls_first=True) が使えますが、
    # それ以前のバージョンやDBによっては annotate と Case/When を使う必要があるかもしれません。
    # ここではシンプルに order_by を使用します。DBによってはNULLの扱いはデフォルトで最後になることがあります。
    # 必要に応じて、より複雑なソートロジックを検討してください。
    purchase_orders_qs = PurchaseOrder.objects.filter(filters).order_by(
        F('expected_arrival').asc(nulls_last=True), 
        'order_number'
    )

    paginated_purchase_orders = paginator.paginate_queryset(purchase_orders_qs, request)
    serializer = PurchaseOrderSerializer(paginated_purchase_orders, many=True)
    
    # DRFのStandardResultsSetPaginationはget_paginated_responseメソッドで
    # 'count', 'next', 'previous', 'results' を含むレスポンスを返します。
    # 'total_pages' や 'current_page' も含めるようにStandardResultsSetPaginationをカスタマイズ済みなので、
    # そのまま paginator.get_paginated_response を使用します。
    return paginator.get_paginated_response(serializer.data)


class PurchaseOrderCreateAjaxAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        instance_id = request.data.get('id')
        instance = None
        message_verb = "登録" # Default for new

        if instance_id:
            try:
                instance = PurchaseOrder.objects.get(pk=instance_id)
                message_verb = "更新"
            except PurchaseOrder.DoesNotExist:
                return Response({'status': 'error', 'message': '指定された入庫予定が見つかりません。'}, status=status.HTTP_404_NOT_FOUND)
        
        # Initialize form with instance if updating, otherwise instance is None for new
        form = PurchaseOrderEntryForm(request.data, instance=instance) 

        if form.is_valid():
            try:
                purchase_order = form.save()
                return JsonResponse({
                    'status': 'success', 
                    'message': f'入庫予定を{message_verb}しました。', 
                    'purchase_order_id': purchase_order.id
                }, status=status.HTTP_200_OK) # Use JsonResponse for direct compatibility if needed, or DRF Response
            except Exception as e:
                # Log the error e for server-side debugging
                print(f"Error saving PurchaseOrder: {str(e)}") 
                return Response({'status': 'error', 'message': f'保存中にエラーが発生しました: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            return Response({'status': 'error', 'errors': form.errors, 'message': '入力内容にエラーがあります。'}, status=status.HTTP_400_BAD_REQUEST)


class PurchaseOrderListAjaxAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        # Using existing get_purchase_orders_api logic might be complex due to pagination differences.
        # For simplicity, a direct query similar to master list views.
        # Note: This doesn't use DRF pagination like get_purchase_orders_api.
        # Consider if the full features of get_purchase_orders_api are needed for this modal.
        # For now, a simpler list for the modal.
        orders = PurchaseOrder.objects.all().order_by('-order_date')[:200] # Limit for performance
        data = [{
            'id': order.id,
            'order_number': order.order_number,
            'supplier': order.supplier,
            'item': order.item,
            'part_number': order.part_number,
            'product_name': order.product_name, # Add product_name for display
            'shipment_number': order.shipment_number or '', # Add shipment_number for display
            'quantity': order.quantity,
            'expected_arrival': order.expected_arrival.strftime('%Y-%m-%d %H:%M') if order.expected_arrival else '',
            'status': order.get_status_display(),
        } for order in orders]
        return Response({'data': data})

class PurchaseOrderDetailAjaxAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk, *args, **kwargs):
        try:
            order = PurchaseOrder.objects.get(pk=pk)
            # Map all relevant fields from PurchaseOrderEntryForm
            data = {
                'id': order.id,
                'order_number': order.order_number,
                'supplier': order.supplier,
                'item': order.item,
                'part_number': order.part_number,
                'product_name': order.product_name,
                'quantity': order.quantity,
                'expected_arrival': order.expected_arrival.strftime('%Y-%m-%dT%H:%M') if order.expected_arrival else None,
                'warehouse': order.warehouse,
                'location': order.location, # Add location
                'parent_part_number': order.parent_part_number,
                'instruction_document': order.instruction_document,
                'shipment_number': order.shipment_number,
                'model_type': order.model_type,
                'is_first_time': order.is_first_time,
                'color_info': order.color_info,
                'delivery_destination': order.delivery_destination,
                'delivery_source': order.delivery_source,
                'remarks1': order.remarks1,
            }
            return Response({'status': 'success', 'data': data})
        except PurchaseOrder.DoesNotExist:
            return Response({'status': 'error', 'message': 'Purchase Order not found'}, status=status.HTTP_404_NOT_FOUND)

class PurchaseOrderDeleteAjaxAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk, *args, **kwargs):
        try:
            order = PurchaseOrder.objects.get(pk=pk)
            order_number = order.order_number
            order.delete()
            return Response({'status': 'success', 'message': f'入庫予定「{order_number}」を削除しました。'})
        except PurchaseOrder.DoesNotExist:
            return Response({'status': 'error', 'message': '指定された入庫予定が見つかりません。'}, status=status.HTTP_404_NOT_FOUND)
        except ProtectedError: # If PurchaseOrder is protected by other models
            return Response({'status': 'error', 'message': 'この入庫予定は他で使用されているため削除できません。'}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_sales_orders_for_issue_api(request):
    """
    出庫予定のSalesOrderをフィルタリングしてページネーション付きで取得するAPI。
    """
    paginator = StandardResultsSetPagination()
    
    filters = Q()

    # 検索パラメータに基づくフィルタリング
    search_order_number = request.query_params.get('search_order_number')
    if search_order_number:
        filters &= Q(order_number__icontains=search_order_number)

    search_item = request.query_params.get('search_item')
    if search_item:
        filters &= Q(item__icontains=search_item)

    search_warehouse = request.query_params.get('search_warehouse')
    if search_warehouse:
        filters &= Q(warehouse__icontains=search_warehouse)

    search_status = request.query_params.get('search_status')
    if search_status:
        filters &= Q(status=search_status)

    sales_orders_qs = SalesOrder.objects.filter(filters).order_by('expected_shipment', 'order_number')

    paginated_sales_orders = paginator.paginate_queryset(sales_orders_qs, request)
    serializer = SalesOrderSerializer(paginated_sales_orders, many=True)
    
    return paginator.get_paginated_response(serializer.data)


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