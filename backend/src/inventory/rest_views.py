from rest_framework import status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination # PageNumberPagination は StandardResultsSetPagination で使用
from rest_framework.views import APIView
from .serializers import (PurchaseOrderSerializer, InventorySerializer, StockMovementSerializer, SalesOrderSerializer, AllocateInventoryForSalesOrderRequestSerializer, ReceiptSerializer)
from .models import PurchaseOrder, Inventory, StockMovement, SalesOrder, Receipt # SalesOrder, Receiptモデルをインポート
from django.http import JsonResponse # JsonResponse をインポート
from django.db import transaction, IntegrityError # トランザクションのためにインポート # Qオブジェクトをインポートして複雑なクエリを構築
from django.db import models
from django.db.models import Q, F
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

# --- ViewSets ---

class ReceiptViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows receipts to be viewed or edited.
    """
    queryset = Receipt.objects.all().select_related('purchase_order', 'operator').order_by('-received_date')
    serializer_class = ReceiptSerializer
    pagination_class = StandardResultsSetPagination
    permission_classes = [IsAuthenticated]

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
            # フロントエンドから 'received' が来た場合、両方の入庫済みステータスを検索対象とする
            if search_status == 'received':
                filters &= Q(status__in=['partially_received', 'fully_received'])
            else:
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

    @action(detail=False, methods=['get'], url_path='distinct-values')
    def distinct_values(self, request):
        """
        指定されたフィールドのユニークな値のリストを返します。
        CharFieldのみを対象とします。
        """
        field_name = request.query_params.get('field')

        # セキュリティ: CharField 型のフィールドのみを許可
        allowed_fields = [f.name for f in PurchaseOrder._meta.get_fields() if isinstance(f, models.CharField)]

        if not field_name or field_name not in allowed_fields:
            return Response({'error': 'Invalid or missing field parameter.'}, status=status.HTTP_400_BAD_REQUEST)

        # 空やNULLでない値のみを取得し、ソートする
        values = PurchaseOrder.objects.filter(**{f'{field_name}__isnull': False}).exclude(**{f'{field_name}': ''}).values_list(field_name, flat=True).distinct().order_by(field_name)

        return Response(list(values))

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