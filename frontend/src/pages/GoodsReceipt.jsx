import React, { useState, useEffect, useCallback } from 'react';
import { getCookie } from '../utils/cookies';
import Modal from '../components/Modal';
import './InventoryInquiry.css'; // 既存のCSSを利用してファイル未発見エラーを回避

const GoodsReceipt = () => {
  // State for purchase orders, pagination, and loading/error status
  const [purchaseOrders, setPurchaseOrders] = useState([]);
  const [pagination, setPagination] = useState({
    count: 0,
    next: null,
    previous: null,
    currentPage: 1,
    totalPages: 1,
  });
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  // State for search filters
  const [filters, setFilters] = useState({
    orderNumber: '',
    supplier: '',
    partNumber: '',
    status: 'pending', // Default to pending orders
  });

  // State for the receipt processing modal
  const [receiptModal, setReceiptModal] = useState({ isOpen: false, order: null, error: '', success: '' });
  const [receiptFormData, setReceiptFormData] = useState({ received_quantity: '', location: '', warehouse: '' });

  // API call to fetch purchase order data
  const fetchPurchaseOrders = useCallback(async (pageUrl = null) => {
    setIsLoading(true);
    setError(null);

    let apiUrl;
    if (pageUrl) {
      apiUrl = pageUrl;
    } else {
      const params = new URLSearchParams();
      if (filters.orderNumber) params.append('search_order_number', filters.orderNumber);
      if (filters.supplier) params.append('search_supplier', filters.supplier);
      if (filters.partNumber) params.append('search_part_number', filters.partNumber);
      if (filters.status) params.append('search_status', filters.status);
      apiUrl = `/api/inventory/purchase-orders/?${params.toString()}`;
    }

    try {
      const response = await fetch(apiUrl);
      if (!response.ok) {
        throw new Error(`Network response was not ok: ${response.statusText}`);
      }
      const data = await response.json();
      setPurchaseOrders(data.results);
      setPagination({
        count: data.count,
        next: data.next,
        previous: data.previous,
        currentPage: data.current_page,
        totalPages: data.total_pages,
      });
    } catch (err) {
      setError('入庫予定データの取得中にエラーが発生しました。');
      console.error('Error fetching purchase order data:', err);
    } finally {
      setIsLoading(false);
    }
  }, [filters]);

  // Initial data fetch on component mount
  useEffect(() => {
    fetchPurchaseOrders();
  }, [fetchPurchaseOrders]);
  
  // Cleanup effect for modal
  useEffect(() => {
    return () => {
      document.body.classList.remove('menu-open-no-scroll');
    };
  }, []);

  // Handlers for filter changes and search
  const handleFilterChange = (e) => {
    const { name, value } = e.target;
    setFilters(prev => ({ ...prev, [name]: value }));
  };

  const handleSearch = () => {
    fetchPurchaseOrders();
  };

  // Modal control functions
  const openReceiptModal = (order) => {
    const remainingQuantity = order.quantity - order.received_quantity;
    setReceiptModal({ isOpen: true, order, error: '', success: '' });
    setReceiptFormData({
      received_quantity: remainingQuantity > 0 ? remainingQuantity : '',
      location: order.location || '',
      warehouse: order.warehouse || '',
    });
    document.body.classList.add('menu-open-no-scroll');
  };

  const closeReceiptModal = () => {
    setReceiptModal({ isOpen: false, order: null, error: '', success: '' });
    document.body.classList.remove('menu-open-no-scroll');
  };

  // Handler for form data changes in the modal
  const handleReceiptFormChange = (e) => {
    const { name, value } = e.target;
    setReceiptFormData(prev => ({ ...prev, [name]: value }));
  };

  // Handler for submitting the receipt form
  const handleReceiptSubmit = async (e) => {
    e.preventDefault();
    setReceiptModal(prev => ({ ...prev, error: '', success: '' }));
    const csrftoken = getCookie('csrftoken');
    
    const receivedQuantity = parseInt(receiptFormData.received_quantity, 10);
    if (isNaN(receivedQuantity) || receivedQuantity <= 0) {
        setReceiptModal(prev => ({ ...prev, error: '入庫数量は正の整数である必要があります。' }));
        return;
    }

    try {
      const response = await fetch('/api/inventory/purchase-receipts/process/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrftoken },
        body: JSON.stringify({
          purchase_order_id: receiptModal.order.id,
          received_quantity: receivedQuantity,
          location: receiptFormData.location.trim(),
          warehouse: receiptFormData.warehouse.trim(),
        }),
      });
      const result = await response.json();
      if (response.ok) {
        setReceiptModal(prev => ({ ...prev, success: `発注 ${result.order_number} の入庫処理が正常に完了しました。` }));
        setTimeout(() => {
          closeReceiptModal();
          fetchPurchaseOrders(); // Refresh data
        }, 1500);
      } else {
        setReceiptModal(prev => ({ ...prev, error: result.error || '入庫処理に失敗しました。' }));
      }
    } catch (err) {
      console.error('Error submitting purchase receipt:', err);
      setReceiptModal(prev => ({ ...prev, error: '入庫処理中に通信エラーが発生しました。' }));
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    return date.toLocaleString('ja-JP', { year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' });
  };

  // Render logic for table body
  const renderTableBody = () => {
    if (isLoading) return <tr><td colSpan="10" className="text-center">検索中...</td></tr>;
    if (error) return <tr><td colSpan="10" className="text-center text-danger">{error}</td></tr>;
    if (purchaseOrders.length === 0) return <tr><td colSpan="10" className="text-center">該当する入庫予定がありません。</td></tr>;

    return purchaseOrders.map(order => (
      <tr key={order.id}>
        <td>{order.order_number}</td>
        <td>{order.supplier || 'N/A'}</td>
        <td>{order.item || 'N/A'}</td>
        <td>{order.product_name || 'N/A'}</td>
        <td className="text-end">{order.quantity}</td>
        <td className="text-end">{order.received_quantity}</td>
        <td className="text-end">{order.quantity - order.received_quantity}</td>
        <td>{formatDate(order.expected_arrival)}</td>
        <td>{order.status === 'pending' ? '未入庫' : order.status === 'received' ? '入庫済み' : 'キャンセル'}</td>
        <td className="text-center">
          <button 
            className="btn btn-sm btn-primary" 
            onClick={() => openReceiptModal(order)}
            disabled={order.status !== 'pending' || (order.quantity - order.received_quantity <= 0)}
          >
            入庫
          </button>
        </td>
      </tr>
    ));
  };

  return (
    <div className="inventory-inquiry goods-receipt">
      <h2 className="inventory-inquiry-title">入庫処置</h2>

      {/* Filters */}
      <div className="goods-receipt-filters d-flex flex-wrap gap-2 align-items-center mb-3">
        <input type="text" name="orderNumber" value={filters.orderNumber} onChange={handleFilterChange} className="form-control" style={{ width: 'auto', flexGrow: 1 }} placeholder="発注番号で検索..." />
        <input type="text" name="supplier" value={filters.supplier} onChange={handleFilterChange} className="form-control" style={{ width: 'auto', flexGrow: 1 }} placeholder="仕入先で検索..." />
        <input type="text" name="partNumber" value={filters.partNumber} onChange={handleFilterChange} className="form-control" style={{ width: 'auto', flexGrow: 1 }} placeholder="品番で検索..." />
        <select name="status" value={filters.status} onChange={handleFilterChange} className="form-select" style={{ width: 'auto' }}>
            <option value="">全てのステータス</option>
            <option value="pending">未入庫</option>
            <option value="received">入庫済み</option>
            <option value="canceled">キャンセル</option>
        </select>
        <button onClick={handleSearch} className="btn btn-primary">検索</button>
      </div>

      {/* Table */}
      <div className="table-responsive">
        <table className="table table-striped table-bordered table-hover mb-0">
          <thead>
            <tr>
              <th>発注番号</th>
              <th>仕入先</th>
              <th>品目</th>
              <th>品名</th>
              <th className="text-end">発注数量</th>
              <th className="text-end">入庫済数量</th>
              <th className="text-end">残数量</th>
              <th>入荷予定日</th>
              <th>ステータス</th>
              <th className="text-center">操作</th>
            </tr>
          </thead>
          <tbody>{renderTableBody()}</tbody>
        </table>
      </div>

      {/* Pagination */}
      <div className="pagination-controls d-flex justify-content-center align-items-center mt-3">
        <button onClick={() => fetchPurchaseOrders(pagination.previous)} className="btn btn-outline-primary" disabled={!pagination.previous}>前へ</button>
        <span className="mx-3">
          {pagination.count > 0 ? `ページ ${pagination.currentPage} / ${pagination.totalPages} (全 ${pagination.count} 件)` : ''}
        </span>
        <button onClick={() => fetchPurchaseOrders(pagination.next)} className="btn btn-outline-primary" disabled={!pagination.next}>次へ</button>
      </div>

      {/* Receipt Processing Modal */}
      <Modal isOpen={receiptModal.isOpen} onClose={closeReceiptModal}>
        <div className="inventory-modal-content">
            <h2>入庫処理</h2>
            <form onSubmit={handleReceiptSubmit}>
              <table className="table table-sm table-bordered mb-3">
                <tbody>
                  <tr>
                    <td style={{ width: '35%' }}><label className="mb-0">発注番号:</label></td>
                    <td><p className="mb-0">{receiptModal.order?.order_number}</p></td>
                  </tr>
                  <tr>
                    <td><label className="mb-0">品名:</label></td>
                    <td><p className="mb-0">{receiptModal.order?.product_name || receiptModal.order?.item}</p></td>
                  </tr>
                  <tr>
                    <td><label className="mb-0">残数量:</label></td>
                    <td><p className="mb-0">{receiptModal.order ? (receiptModal.order.quantity - receiptModal.order.received_quantity) : ''}</p></td>
                  </tr>
                  <tr>
                    <td><label htmlFor="modal_received_quantity_input" className="mb-0">入庫数量:</label></td>
                    <td><input type="number" id="modal_received_quantity_input" name="received_quantity" value={receiptFormData.received_quantity} onChange={handleReceiptFormChange} className="form-control form-control-sm text-end" required min="1" max={receiptModal.order ? (receiptModal.order.quantity - receiptModal.order.received_quantity) : undefined} /></td>
                  </tr>
                  <tr>
                    <td><label htmlFor="modal_warehouse_input" className="mb-0">入庫倉庫:</label></td>
                    <td><input type="text" id="modal_warehouse_input" name="warehouse" value={receiptFormData.warehouse} onChange={handleReceiptFormChange} className="form-control form-control-sm" placeholder="POの倉庫 (変更可)" /></td>
                  </tr>
                  <tr>
                    <td><label htmlFor="modal_location_input" className="mb-0">入庫棚番:</label></td>
                    <td><input type="text" id="modal_location_input" name="location" value={receiptFormData.location} onChange={handleReceiptFormChange} className="form-control form-control-sm" placeholder="POの棚番 (変更可)" /></td>
                  </tr>
                </tbody>
              </table>
              {receiptModal.error && <div className="alert alert-danger">{receiptModal.error}</div>}
              {receiptModal.success && <div className="alert alert-success">{receiptModal.success}</div>}
              <div className="mt-3 text-end">
                <button type="submit" className="btn btn-primary btn-sm">入庫実行</button>
                <button type="button" className="btn btn-secondary btn-sm ms-2" onClick={closeReceiptModal}>キャンセル</button>
              </div>
            </form>
        </div>
      </Modal>
    </div>
  );
};

export default GoodsReceipt;