import React, { useState, useEffect, useCallback } from 'react';
import { getCookie } from '../utils/cookies';
import Modal from '../components/Modal';

const GoodsIssue = () => {
  const [salesOrders, setSalesOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Modal state
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [selectedOrder, setSelectedOrder] = useState(null);
  const [issueQuantity, setIssueQuantity] = useState('');
  const [modalMessage, setModalMessage] = useState({ text: '', type: '' }); // type: 'success' or 'danger'

  const fetchSalesOrders = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch('/api/inventory/sales-orders/?search_status=pending');
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      setSalesOrders(data.results || []);
    } catch (e) {
      setError('出庫待ち受注の読み込みに失敗しました。');
      console.error("Fetch error:", e);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchSalesOrders();
  }, [fetchSalesOrders]);

  const openModal = (order) => {
    setSelectedOrder(order);
    setIssueQuantity(order.remaining_quantity > 0 ? order.remaining_quantity.toString() : '');
    setModalMessage({ text: '', type: '' });
    setIsModalOpen(true);
  };

  const closeModal = () => {
    setIsModalOpen(false);
    setSelectedOrder(null);
    setIssueQuantity('');
    setModalMessage({ text: '', type: '' });
  };

  const handleIssueSubmit = async (e) => {
    e.preventDefault();
    setModalMessage({ text: '', type: '' });

    const quantityToShip = parseInt(issueQuantity, 10);
    if (isNaN(quantityToShip) || quantityToShip <= 0) {
      setModalMessage({ text: '出庫数量は1以上の正の整数である必要があります。', type: 'danger' });
      return;
    }
    if (quantityToShip > selectedOrder.remaining_quantity) {
      setModalMessage({ text: '出庫数量が残数量を超えています。', type: 'danger' });
      return;
    }

    const csrfToken = getCookie('csrftoken');

    try {
      const response = await fetch('/api/inventory/sales-orders/issue/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': csrfToken,
        },
        body: JSON.stringify({
          order_id: selectedOrder.id,
          quantity_to_ship: quantityToShip,
        }),
      });

      const data = await response.json();

      if (response.ok && data.success) {
        setModalMessage({ text: data.message || '出庫処理が正常に完了しました。', type: 'success' });
        setTimeout(() => {
          closeModal();
          fetchSalesOrders(); // Refresh the list
        }, 1500);
      } else {
        setModalMessage({ text: data.error || 'エラーが発生しました。', type: 'danger' });
      }
    } catch (err) {
      console.error('Error:', err);
      setModalMessage({ text: '通信エラーが発生しました。', type: 'danger' });
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return '-';
    return dateString.split('T')[0];
  };

  const renderTableBody = () => {
    if (loading) {
      return <tr><td colSpan="8" className="text-center">読み込み中...</td></tr>;
    }
    if (error) {
      return <tr><td colSpan="8" className="text-center text-danger">{error}</td></tr>;
    }
    if (salesOrders.length === 0) {
      return <tr><td colSpan="8" className="text-center">出庫待ちの受注はありません。</td></tr>;
    }
    return salesOrders.map(order => (
      <tr key={order.id}>
        <td>{order.order_number || '-'}</td>
        <td>{order.item || '-'}</td>
        <td>{order.warehouse || '-'}</td>
        <td className="text-end">{order.quantity}</td>
        <td className="text-end">{order.shipped_quantity}</td>
        <td className="text-end">{order.remaining_quantity}</td>
        <td>{formatDate(order.expected_shipment)}</td>
        <td className="text-center">
          <button
            className="btn btn-sm btn-primary"
            onClick={() => openModal(order)}
            disabled={order.remaining_quantity <= 0}
          >
            出庫
          </button>
        </td>
      </tr>
    ));
  };

  return (
    <div>
      <h2>出庫処理</h2>
      <div className="table-responsive">
        <table className="table table-striped table-bordered table-hover table-sm">
          <thead className="table-light">
            <tr>
              <th>受注番号</th>
              <th>品目</th>
              <th>倉庫</th>
              <th className="text-end">予定数量</th>
              <th className="text-end">済数量</th>
              <th className="text-end">残数量</th>
              <th>出庫予定日</th>
              <th className="text-center">アクション</th>
            </tr>
          </thead>
          <tbody>
            {renderTableBody()}
          </tbody>
        </table>
      </div>

      {selectedOrder && (
        <Modal isOpen={isModalOpen} onClose={closeModal}>
          <div className="inventory-modal-content">
            <h2>出庫処理</h2>
            <form onSubmit={handleIssueSubmit}>
              <div className="mb-2"><strong>受注番号:</strong> {selectedOrder.order_number}</div>
              <div className="mb-2"><strong>品目:</strong> {selectedOrder.item}</div>
              <div className="mb-2"><strong>倉庫:</strong> {selectedOrder.warehouse}</div>
              <div className="mb-3"><strong>残数量:</strong> {selectedOrder.remaining_quantity}</div>
              
              <div className="mb-3">
                <label htmlFor="quantity_to_ship" className="form-label">出庫数量:</label>
                <input
                  type="number"
                  id="quantity_to_ship"
                  name="quantity_to_ship"
                  className="form-control"
                  value={issueQuantity}
                  onChange={(e) => setIssueQuantity(e.target.value)}
                  min="1"
                  max={selectedOrder.remaining_quantity}
                  required
                  placeholder={`最大 ${selectedOrder.remaining_quantity}`}
                />
              </div>

              {modalMessage.text && (
                <div className={`alert alert-${modalMessage.type}`}>
                  {modalMessage.text}
                </div>
              )}

              <div className="mt-3 text-end">
                <button type="submit" className="btn btn-primary">確認</button>
                <button type="button" className="btn btn-secondary ms-2" onClick={closeModal}>キャンセル</button>
              </div>
            </form>
          </div>
        </Modal>
      )}
    </div>
  );
};

export default GoodsIssue;