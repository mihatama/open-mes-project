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
  const [displaySettings, setDisplaySettings] = useState([]); // For dynamic columns
  const [searchFields, setSearchFields] = useState([]); // State for dynamic search fields

  // State for search filters
  const [filters, setFilters] = useState({
    // Dynamic fields will be added here
    status: 'pending', // Default to pending orders
  });

  // State for the receipt processing modal
  const [receiptModal, setReceiptModal] = useState({ isOpen: false, order: null, error: '', success: '' });
  const [receiptFormData, setReceiptFormData] = useState({ received_quantity: '', location: '', warehouse: '' });

  // API call to fetch purchase order data and display settings
  const fetchPurchaseOrders = useCallback(async (pageUrl = null) => {
    setIsLoading(true);
    setError(null);

    let dataApiUrl;
    if (pageUrl) {
      try {
        // APIが返す完全なURLから、ホスト名を除いたパス部分だけを取得する
        const url = new URL(pageUrl);
        dataApiUrl = url.pathname + url.search;
      } catch (e) {
        dataApiUrl = pageUrl; // パースに失敗した場合はそのまま使用
      }
    } else {
      const params = new URLSearchParams();
      // Dynamic filter parameter construction
      for (const [key, value] of Object.entries(filters)) {
        if (value) {
          params.append(`search_${key}`, value);
        }
      }
      dataApiUrl = `/api/inventory/purchase-orders/?${params.toString()}`;
    }

    // 「入庫処置」ページは入庫予定(purchase_order)と入庫実績(goods_receipt)の両方の設定を参照する
    const poSettingsUrl = '/api/base/model-display-settings/?data_type=purchase_order';
    const grSettingsUrl = '/api/base/model-display-settings/?data_type=goods_receipt';
    const poFieldsUrl = '/api/base/model-fields/?data_type=purchase_order';
    const grFieldsUrl = '/api/base/model-fields/?data_type=goods_receipt';

    try {
      const [poSettingsResponse, grSettingsResponse, dataResponse, poFieldsResponse, grFieldsResponse] = await Promise.all([
        fetch(poSettingsUrl, { credentials: 'include' }),
        fetch(grSettingsUrl, { credentials: 'include' }),
        fetch(dataApiUrl, { credentials: 'include' }),
        fetch(poFieldsUrl, { credentials: 'include' }),
        fetch(grFieldsUrl, { credentials: 'include' }),
      ]);

      // レスポンスのJSONボディは一度しか読み取れないため、先にパースして変数に格納します
      const poSettings = poSettingsResponse.ok ? await poSettingsResponse.json() : [];
      const grSettings = grSettingsResponse.ok ? await grSettingsResponse.json() : [];
      const poFields = poFieldsResponse.ok ? await poFieldsResponse.json() : [];
      const grFields = grFieldsResponse.ok ? await grFieldsResponse.json() : [];

      // model-fields をマージして、model_field_name -> verbose_name のマップを作成
      const verboseNameMap = new Map();
      const fieldTypeMap = new Map();

      poFields.forEach(field => {
        verboseNameMap.set(field.name, field.verbose_name);
        fieldTypeMap.set(field.name, field.field_type);
      });
      grFields.forEach(field => {
          if (!verboseNameMap.has(field.name)) {
              verboseNameMap.set(field.name, field.verbose_name);
              fieldTypeMap.set(field.name, field.field_type);
          }
      });

      if (poSettingsResponse.ok && grSettingsResponse.ok) {
        // 両方の設定をマージする。同じフィールド名がある場合は入庫実績(grSettings)を優先する
        const settingsMap = new Map();
        poSettings.forEach(setting => {
            settingsMap.set(setting.model_field_name, setting);
        });
        grSettings.forEach(setting => {
            settingsMap.set(setting.model_field_name, setting);
        });

        const mergedSettings = Array.from(settingsMap.values());

        // マージした設定に verbose_name と field_type を追加
        const combinedSettings = mergedSettings.map(setting => ({
            ...setting,
            verbose_name: verboseNameMap.get(setting.model_field_name) || setting.model_field_name,
            field_type: fieldTypeMap.get(setting.model_field_name) || 'Unknown',
        }));

        const visibleColumns = combinedSettings
          .filter(s => s.is_list_display)
          .sort((a, b) => a.display_order - b.display_order);
        setDisplaySettings(visibleColumns);

        const searchableFields = combinedSettings
          .filter(s => s.is_search_field)
          .sort((a, b) => a.search_order - b.search_order);
        setSearchFields(searchableFields);

      } else {
        console.error('表示設定の取得に失敗しました。');
        // Fallback to empty, which will render default columns
        setDisplaySettings([]);
        setSearchFields([]);
      }

      if (!dataResponse.ok) {
        throw new Error(`Network response was not ok: ${dataResponse.statusText}`);
      }
      const data = await dataResponse.json();
      setPurchaseOrders(data.results);
      setPagination({
        count: data.count,
        next: data.next,
        previous: data.previous,
        currentPage: data.current_page,
        totalPages: data.total_pages,
      });
    } catch (err) {
      setError('データの取得中にエラーが発生しました。');
      console.error('Error fetching data:', err);
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
      const response = await fetch('/api/inventory/purchase-orders/process-receipt/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrftoken },
        body: JSON.stringify({
          purchase_order_id: receiptModal.order.id,
          received_quantity: receivedQuantity,
          location: receiptFormData.location.trim(),
          warehouse: receiptFormData.warehouse.trim(),
        }),
        credentials: 'include',
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

  // Render logic for table headers
  const renderTableHeaders = () => {
    const defaultHeaders = (
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
    );

    if (isLoading || displaySettings.length === 0) {
      return defaultHeaders;
    }

    return (
      <tr>
        {displaySettings.map(setting => {
          const isNumeric = ['quantity', 'received_quantity', 'remaining_quantity'].includes(setting.model_field_name);
          // カスタム表示名がスペースのみの場合も考慮してtrim()し、
          // verbose_nameがなければmodel_field_nameをフォールバックとして使用
          const headerText = (setting.display_name || '').trim() || setting.verbose_name || setting.model_field_name;
          return (
            <th key={setting.model_field_name} className={isNumeric ? 'text-end' : ''}>
              {headerText}
            </th>
          );
        })}
        <th className="text-center">操作</th>
      </tr>
    );
  };

  // Render logic for table body
  const renderTableBody = () => {
    if (isLoading) return <tr><td colSpan="10" className="text-center">検索中...</td></tr>;
    if (error) return <tr><td colSpan="10" className="text-center text-danger">{error}</td></tr>;
    if (purchaseOrders.length === 0) return <tr><td colSpan="10" className="text-center">該当する入庫予定がありません。</td></tr>;

    return purchaseOrders.map(order => {
      const cells = displaySettings.map(setting => {
        const fieldName = setting.model_field_name;
        let cellValue;

        // Handle special cases and formatting
        if (fieldName === 'remaining_quantity') {
          cellValue = order.quantity - order.received_quantity;
        } else if (fieldName === 'expected_arrival' || fieldName === 'order_date') {
          cellValue = formatDate(order[fieldName]);
        } else if (fieldName === 'status') {
          const statusMap = {
            pending: '未入庫',
            partially_received: '一部入庫',
            fully_received: '全量入庫済み',
            canceled: 'キャンセル',
          };
          cellValue = statusMap[order.status] || order.status;
        } else {
          cellValue = order[fieldName];
        }

        const isNumeric = ['quantity', 'received_quantity', 'remaining_quantity'].includes(fieldName);
        const className = isNumeric ? 'text-end' : '';

        return <td key={fieldName} className={className}>{cellValue ?? 'N/A'}</td>;
      });

      return (
        <tr key={order.id}>
          {cells}
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
      );
    });
  };

  return (
    <div className="inventory-inquiry goods-receipt">
      <h2 className="inventory-inquiry-title">入庫処置</h2>

      {/* Filters */}
      <div className="goods-receipt-filters d-flex flex-wrap gap-2 align-items-center mb-3">
        {searchFields
          .filter(field => field.model_field_name !== 'status') // statusは固定で表示するので除外
          .map(field => (
            <input
              key={field.model_field_name}
              type="text"
              name={field.model_field_name}
              value={filters[field.model_field_name] || ''}
              onChange={handleFilterChange}
              className="form-control"
              style={{ width: 'auto', flexGrow: 1 }}
              placeholder={`${field.verbose_name}で検索...`}
            />
          ))
        }
        <select name="status" value={filters.status} onChange={handleFilterChange} className="form-select" style={{ width: 'auto' }}>
            <option value="">全てのステータス</option>
            <option value="pending">未入庫</option>
            <option value="partially_received">一部入庫</option>
            <option value="fully_received">全量入庫済み</option>
            <option value="canceled">キャンセル</option>
        </select>
        <button onClick={handleSearch} className="btn btn-primary">検索</button>
      </div>

      {/* Table */}
      <div className="table-responsive">
        <table className="table table-striped table-bordered table-hover mb-0">
          <thead>
            {renderTableHeaders()}
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