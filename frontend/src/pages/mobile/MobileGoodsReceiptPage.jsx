import React, { useState, useEffect, useCallback } from 'react';
import { getCookie } from '../../utils/cookies';
import './MobileGoodsReceiptPage.css';

const MobileGoodsReceiptPage = () => {
  // State for purchase orders, loading/error status
  const [purchaseOrders, setPurchaseOrders] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  // State for search
  const [searchTerm, setSearchTerm] = useState('');

  // State for the receipt processing form (acting as a modal)
  const [selectedOrder, setSelectedOrder] = useState(null);
  const [receiptFormData, setReceiptFormData] = useState({ received_quantity: '', location: '', warehouse: '' });
  const [formError, setFormError] = useState('');
  const [formSuccess, setFormSuccess] = useState('');

  // API call to fetch purchase order data
  const fetchPurchaseOrders = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    const params = new URLSearchParams();
    if (searchTerm) {
      // This assumes the backend has a generic search filter that checks multiple fields (e.g., order_number, part_number).
      params.append('search', searchTerm);
    }
    params.append('search_status', 'pending'); // Mobile view is for pending receipts
    const apiUrl = `/api/inventory/schedules/data/?${params.toString()}`;

    try {
      const response = await fetch(apiUrl);
      if (!response.ok) {
        throw new Error(`Network response was not ok: ${response.statusText}`);
      }
      const data = await response.json();
      setPurchaseOrders(data.results);
    } catch (err) {
      setError('入庫予定データの取得中にエラーが発生しました。');
      console.error('Error fetching purchase order data:', err);
    } finally {
      setIsLoading(false);
    }
  }, [searchTerm]);

  // Initial data fetch and on search term change (debounced)
  useEffect(() => {
    const handler = setTimeout(() => {
      fetchPurchaseOrders();
    }, 500);
    return () => clearTimeout(handler);
  }, [searchTerm, fetchPurchaseOrders]);

  // Handlers for form
  const openReceiptForm = (order) => {
    const remainingQuantity = order.quantity - order.received_quantity;
    setSelectedOrder(order);
    setReceiptFormData({
      received_quantity: remainingQuantity > 0 ? remainingQuantity : '',
      location: order.location || '',
      warehouse: order.warehouse || '',
    });
    setFormError('');
    setFormSuccess('');
  };

  const closeReceiptForm = () => {
    setSelectedOrder(null);
  };

  const handleReceiptFormChange = (e) => {
    const { name, value } = e.target;
    setReceiptFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleReceiptSubmit = async (e) => {
    e.preventDefault();
    setFormError('');
    setFormSuccess('');
    const csrftoken = getCookie('csrftoken');

    const receivedQuantity = parseInt(receiptFormData.received_quantity, 10);
    if (isNaN(receivedQuantity) || receivedQuantity <= 0) {
      setFormError('入庫数量は正の整数である必要があります。');
      return;
    }
    if (selectedOrder && receivedQuantity > (selectedOrder.quantity - selectedOrder.received_quantity)) {
      setFormError('入庫数量が残数量を超えています。');
      return;
    }

    try {
      const response = await fetch('/api/inventory/purchase-receipts/process/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrftoken },
        body: JSON.stringify({
          purchase_order_id: selectedOrder.id,
          received_quantity: receivedQuantity,
          location: receiptFormData.location.trim(),
          warehouse: receiptFormData.warehouse.trim(),
        }),
      });
      const result = await response.json();
      if (response.ok) {
        setFormSuccess(`発注 ${result.order_number} の入庫処理が正常に完了しました。`);
        setTimeout(() => {
          closeReceiptForm();
          fetchPurchaseOrders(); // Refresh data
        }, 1500);
      } else {
        setFormError(result.error || '入庫処理に失敗しました。');
      }
    } catch (err) {
      console.error('Error submitting purchase receipt:', err);
      setFormError('入庫処理中に通信エラーが発生しました。');
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleDateString('ja-JP');
  };

  const renderOrderList = () => {
    if (isLoading) return <div className="text-center p-3">検索中...</div>;
    if (error) return <div className="alert alert-danger">{error}</div>;
    if (purchaseOrders.length === 0) return <div className="text-center p-3">該当する未入庫の予定がありません。</div>;

    return (
      <div className="list-group">
        {purchaseOrders.map(order => (
          <div key={order.id} className="list-group-item list-group-item-action">
            <div className="d-flex w-100 justify-content-between">
              <h5 className="mb-1">{order.product_name || order.item}</h5>
              <small>予定日: {formatDate(order.expected_arrival)}</small>
            </div>
            <p className="mb-1">発注番号: {order.order_number}</p>
            <p className="mb-1">残数量: {order.quantity - order.received_quantity} / {order.quantity}</p>
            <button
              className="btn btn-primary btn-sm mt-2"
              onClick={() => openReceiptForm(order)}
              disabled={order.quantity - order.received_quantity <= 0}
            >
              入庫処理
            </button>
          </div>
        ))}
      </div>
    );
  };

  const renderReceiptForm = () => {
    if (!selectedOrder) return null;

    return (
      <div className="mobile-receipt-modal-overlay">
        <div className="mobile-receipt-modal-content">
          <div className="d-flex justify-content-between align-items-center">
            <h4>入庫処理</h4>
            <button onClick={closeReceiptForm} className="btn-close"></button>
          </div>
          <hr />
          <form onSubmit={handleReceiptSubmit}>
            <p><strong>発注番号:</strong> {selectedOrder.order_number}</p>
            <p><strong>品名:</strong> {selectedOrder.product_name || selectedOrder.item}</p>
            <p><strong>残数量:</strong> {selectedOrder.quantity - selectedOrder.received_quantity}</p>
            <div className="mb-3"><label htmlFor="received_quantity" className="form-label">入庫数量</label><input type="number" id="received_quantity" name="received_quantity" value={receiptFormData.received_quantity} onChange={handleReceiptFormChange} className="form-control text-end" required min="1" max={selectedOrder.quantity - selectedOrder.received_quantity} /></div>
            <div className="mb-3"><label htmlFor="warehouse" className="form-label">入庫倉庫</label><input type="text" id="warehouse" name="warehouse" value={receiptFormData.warehouse} onChange={handleReceiptFormChange} className="form-control" placeholder="倉庫" /></div>
            <div className="mb-3"><label htmlFor="location" className="form-label">入庫棚番</label><input type="text" id="location" name="location" value={receiptFormData.location} onChange={handleReceiptFormChange} className="form-control" placeholder="棚番" /></div>
            {formError && <div className="alert alert-danger">{formError}</div>}
            {formSuccess && <div className="alert alert-success">{formSuccess}</div>}
            <div className="d-grid gap-2 mt-4"><button type="submit" className="btn btn-primary">入庫実行</button><button type="button" className="btn btn-secondary" onClick={closeReceiptForm}>キャンセル</button></div>
          </form>
        </div>
      </div>
    );
  };

  return (
    <div className="mobile-goods-receipt-page">
      <h2 className="page-title">入庫処理</h2>
      <div className="mb-3"><input type="search" className="form-control" placeholder="発注番号などで検索..." value={searchTerm} onChange={(e) => setSearchTerm(e.target.value)} /></div>
      {renderOrderList()}
      {renderReceiptForm()}
    </div>
  );
};

export default MobileGoodsReceiptPage;