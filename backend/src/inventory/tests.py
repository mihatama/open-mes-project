from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from .models import Inventory, PurchaseOrder

User = get_user_model()

class InventoryAPITests(APITestCase):
    def setUp(self):
        """テストの初期設定"""
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.client.force_authenticate(user=self.user)

        self.inventory1 = Inventory.objects.create(part_number='PART-001', warehouse='WH-A', location='A-01', quantity=100)
        self.inventory2 = Inventory.objects.create(part_number='PART-002', warehouse='WH-B', location='B-01', quantity=50)

    def test_list_inventories(self):
        """在庫一覧を取得できることを確認"""
        url = reverse('inventory_api:inventory-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)
        self.assertEqual(response.data['results'][0]['part_number'], self.inventory1.part_number)

    def test_retrieve_inventory(self):
        """特定の在庫を取得できることを確認"""
        url = reverse('inventory_api:inventory-detail', kwargs={'pk': self.inventory1.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['quantity'], 100)

    def test_filter_inventory_by_part_number(self):
        """品番で在庫をフィルタリングできることを確認"""
        url = reverse('inventory_api:inventory-list')
        response = self.client.get(url, {'part_number_query': 'PART-001'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['part_number'], 'PART-001')


class PurchaseOrderAPITests(APITestCase):
    def setUp(self):
        """テストの初期設定"""
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.client.force_authenticate(user=self.user)

        self.po1 = PurchaseOrder.objects.create(order_number='PO-001', item='Item A', quantity=10)
        self.po2 = PurchaseOrder.objects.create(order_number='PO-002', item='Item B', quantity=20, status='received')

    def test_list_purchase_orders(self):
        """入庫予定一覧を取得できることを確認"""
        url = reverse('inventory_api:purchaseorder-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)

    def test_create_purchase_order(self):
        """新しい入庫予定を作成できることを確認"""
        url = reverse('inventory_api:purchaseorder-list')
        data = {'order_number': 'PO-003', 'item': 'Item C', 'quantity': 30}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(PurchaseOrder.objects.count(), 3)

    def test_create_purchase_order_with_duplicate_number(self):
        """重複した発注番号で作成できないことを確認"""
        url = reverse('inventory_api:purchaseorder-list')
        data = {'order_number': 'PO-001', 'item': 'Item D', 'quantity': 40}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('order_number', response.data)

    def test_delete_purchase_order(self):
        """入庫予定を削除できることを確認"""
        url = reverse('inventory_api:purchaseorder-detail', kwargs={'pk': self.po1.id})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(PurchaseOrder.objects.count(), 1)
