import React, { useState, useEffect, useCallback } from 'react';
import authFetch from '../utils/api';

const ShipmentSchedule = () => {
  const [salesOrders, setSalesOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchSalesOrders = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      // This API endpoint is used in other parts of the app (e.g., mobile goods issue)
      // to fetch sales orders. We filter by 'pending' status to get the shipment schedule.
      const response = await authFetch('/api/inventory/sales-orders/?search_status=pending');
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      // The API returns a paginated response with a 'results' key.
      setSalesOrders(data.results || []);
    } catch (e) {
      setError('出庫予定の読み込みに失敗しました。');
      console.error("Fetch error:", e);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchSalesOrders();
  }, [fetchSalesOrders]);

  const formatDate = (dateString) => {
    if (!dateString) return '';
    const date = new Date(dateString);
    // Format to 'YYYY-MM-DD HH:mm'
    return date.toISOString().slice(0, 16).replace('T', ' ');
  };

  const renderTableBody = () => {
    if (loading) {
      return <tr><td colSpan="9" className="text-center">読み込み中...</td></tr>;
    }
    if (error) {
      return <tr><td colSpan="9" className="text-center text-danger">{error}</td></tr>;
    }
    if (salesOrders.length === 0) {
      return <tr><td colSpan="9" className="text-center">出庫予定はありません。</td></tr>;
    }
    return salesOrders.map(order => (
      <tr key={order.id}>
        <td>{order.order_number || ''}</td>
        <td>{order.item || ''}</td>
        <td className="text-end">{order.quantity || ''}</td>
        <td className="text-end">{order.shipped_quantity || ''}</td>
        <td>{formatDate(order.order_date)}</td>
        <td>{formatDate(order.expected_shipment)}</td>
        <td>{order.shipment_number || ''}</td>
        <td>{order.warehouse || ''}</td>
        <td>{order.status_display || ''}</td>
      </tr>
    ));
  };

  return (
    <div>
      <h2>出庫予定一覧</h2>
      <div className="table-responsive">
        <table className="table table-striped table-bordered table-hover table-sm">
          <thead className="table-light">
            <tr>
              <th>受注番号</th>
              <th>製品/材料</th>
              <th className="text-end">出庫予定数量</th>
              <th className="text-end">実際に出庫した数量</th>
              <th>受注日</th>
              <th>出庫予定日</th>
              <th>便番号</th>
              <th>倉庫</th>
              <th>ステータス</th>
            </tr>
          </thead>
          <tbody>
            {renderTableBody()}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default ShipmentSchedule;