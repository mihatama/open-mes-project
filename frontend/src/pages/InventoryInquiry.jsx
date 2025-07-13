import React, { useState, useEffect, useCallback } from 'react';
import { getCookie } from '../utils/cookies';
import Modal from '../components/Modal';
import './InventoryInquiry.css';

const InventoryInquiry = () => {
  // State for inventory data, pagination, and loading/error status
  const [inventory, setInventory] = useState([]);
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
    partNumber: '',
    warehouse: '',
    location: '',
    hideZeroStock: true,
  });

  // State for modals
  const [modifyModal, setModifyModal] = useState({ isOpen: false, item: null, error: '', success: '' });
  const [moveModal, setMoveModal] = useState({ isOpen: false, item: null, error: '', success: '' });

  // State for form data within modals
  const [modifyFormData, setModifyFormData] = useState({ warehouse: '', location: '', quantity: 0 });
  const [moveFormData, setMoveFormData] = useState({ quantity_to_move: 0, target_warehouse: '', target_location: '' });

  // API call to fetch inventory data
  const fetchInventory = useCallback(async (pageUrl = null) => {
    setIsLoading(true);
    setError(null);

    let apiUrl;
    if (pageUrl) {
      // Use the full URL provided by the API for next/previous pages
      apiUrl = pageUrl;
    } else {
      const params = new URLSearchParams();
      if (filters.partNumber) params.append('part_number_query', filters.partNumber);
      if (filters.warehouse) params.append('warehouse_query', filters.warehouse);
      if (filters.location) params.append('location_query', filters.location);
      params.append('hide_zero_stock_query', filters.hideZeroStock);
      apiUrl = `/api/inventory/data/?${params.toString()}`;
    }

    try {
      const response = await fetch(apiUrl);
      if (!response.ok) {
        throw new Error(`Network response was not ok: ${response.statusText}`);
      }
      const data = await response.json();
      setInventory(data.results);
      setPagination({
        count: data.count,
        next: data.next,
        previous: data.previous,
        currentPage: data.current_page,
        totalPages: data.total_pages,
      });
    } catch (err) {
      setError('在庫データの取得中にエラーが発生しました。');
      console.error('Error fetching inventory data:', err);
    } finally {
      setIsLoading(false);
    }
  }, [filters]); // Recreate this function only if filters change

  // Initial data fetch on component mount
  useEffect(() => {
    fetchInventory();
  }, [fetchInventory]);

  // Cleanup effect to remove body class on unmount
  useEffect(() => {
    return () => {
      document.body.classList.remove('menu-open-no-scroll');
    };
  }, []);

  // Handlers for filter changes and search
  const handleFilterChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFilters(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value,
    }));
  };

  const handleSearch = () => {
    fetchInventory();
  };

  // Modal control functions
  const openModifyModal = (item) => {
    setModifyModal({ isOpen: true, item, error: '', success: '' });
    setModifyFormData({
      warehouse: item.warehouse,
      location: item.location === '-' ? '' : item.location,
      quantity: item.quantity,
    });
    document.body.classList.add('menu-open-no-scroll');
  };

  const closeModifyModal = () => {
    setModifyModal({ isOpen: false, item: null, error: '', success: '' });
    document.body.classList.remove('menu-open-no-scroll');
  };

  const openMoveModal = (item) => {
    setMoveModal({ isOpen: true, item, error: '', success: '' });
    setMoveFormData({
      quantity_to_move: item.quantity, // Default to moving all
      target_warehouse: '',
      target_location: '',
    });
    document.body.classList.add('menu-open-no-scroll');
  };

  const closeMoveModal = () => {
    setMoveModal({ isOpen: false, item: null, error: '', success: '' });
    document.body.classList.remove('menu-open-no-scroll');
  };

  // Handlers for form data changes in modals
  const handleModifyFormChange = (e) => {
    const { name, value } = e.target;
    setModifyFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleMoveFormChange = (e) => {
    const { name, value } = e.target;
    setMoveFormData(prev => ({ ...prev, [name]: value }));
  };

  // Handler for submitting the modify form
  const handleModifySubmit = async (e) => {
    e.preventDefault();
    setModifyModal(prev => ({ ...prev, error: '', success: '' }));
    const csrftoken = getCookie('csrftoken');
    try {
      const response = await fetch('/api/inventory/update/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrftoken },
        body: JSON.stringify({
          inventory_id: modifyModal.item.id,
          quantity: modifyFormData.quantity,
          warehouse: modifyFormData.warehouse.trim(),
          location: modifyFormData.location.trim(),
        }),
      });
      const result = await response.json();
      if (result.success) {
        setModifyModal(prev => ({ ...prev, success: result.message || '在庫を更新しました。' }));
        setTimeout(() => {
          closeModifyModal();
          fetchInventory(); // Refresh data
        }, 1500);
      } else {
        setModifyModal(prev => ({ ...prev, error: result.error || '在庫の更新に失敗しました。' }));
      }
    } catch (err) {
      console.error('Error submitting inventory update:', err);
      setModifyModal(prev => ({ ...prev, error: '在庫更新中に通信エラーが発生しました。' }));
    }
  };

  // Handler for submitting the move form
  const handleMoveSubmit = async (e) => {
    e.preventDefault();
    setMoveModal(prev => ({ ...prev, error: '', success: '' }));
    const quantityToMove = parseInt(moveFormData.quantity_to_move, 10);
    if (quantityToMove <= 0) {
      setMoveModal(prev => ({ ...prev, error: '移動数量は1以上である必要があります。' }));
      return;
    }
    if (!moveFormData.target_warehouse) {
      setMoveModal(prev => ({ ...prev, error: '移動先倉庫は必須です。' }));
      return;
    }
    const csrftoken = getCookie('csrftoken');
    try {
      const response = await fetch('/api/inventory/move/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrftoken },
        body: JSON.stringify({
          source_inventory_id: moveModal.item.id,
          quantity_to_move: quantityToMove,
          target_warehouse: moveFormData.target_warehouse.trim(),
          target_location: moveFormData.target_location.trim(),
        }),
      });
      const result = await response.json();
      if (result.success) {
        setMoveModal(prev => ({ ...prev, success: result.message || '在庫を移動しました。' }));
        setTimeout(() => {
          closeMoveModal();
          fetchInventory(); // Refresh data
        }, 1500);
      } else {
        setMoveModal(prev => ({ ...prev, error: result.error || '在庫の移動に失敗しました。' }));
      }
    } catch (err) {
      console.error('Error submitting inventory move:', err);
      setMoveModal(prev => ({ ...prev, error: '在庫移動中に通信エラーが発生しました。' }));
    }
  };

  // Render logic for table body
  const renderTableBody = () => {
    if (isLoading) return <tr><td colSpan="8" className="text-center">検索中...</td></tr>;
    if (error) return <tr><td colSpan="8" className="text-center text-danger">{error}</td></tr>;
    if (inventory.length === 0) return <tr><td colSpan="8" className="text-center">該当する在庫情報がありません。</td></tr>;

    return inventory.map(item => (
      <tr key={item.id}>
        <td>{item.part_number || 'N/A'}</td>
        <td>{item.warehouse || 'N/A'}</td>
        <td>{item.location || '-'}</td>
        <td className="text-end">{item.quantity}</td>
        <td className="text-end">{item.reserved}</td>
        <td className="text-end">{item.available_quantity}</td>
        <td>{item.last_updated ? new Date(item.last_updated).toLocaleString() : 'N/A'}</td>
        <td className="text-center">
          <button className="btn btn-sm btn-info ms-1" onClick={() => openMoveModal(item)}>移動</button>
          <button className="btn btn-sm btn-warning ms-1" onClick={() => openModifyModal(item)}>修正</button>
        </td>
      </tr>
    ));
  };

  return (
    <div className="inventory-inquiry">
      <h2 className="inventory-inquiry-title">在庫照会</h2>

      {/* Filters */}
      <div className="inventory-filters d-flex flex-wrap gap-2 align-items-center mb-3">
        <input type="text" name="partNumber" value={filters.partNumber} onChange={handleFilterChange} className="form-control" style={{ width: 'auto', flexGrow: 1 }} placeholder="製品/材料名で検索..." />
        <input type="text" name="warehouse" value={filters.warehouse} onChange={handleFilterChange} className="form-control" style={{ width: 'auto', flexGrow: 1 }} placeholder="倉庫で検索..." />
        <input type="text" name="location" value={filters.location} onChange={handleFilterChange} className="form-control" style={{ width: 'auto', flexGrow: 1 }} placeholder="場所で検索..." />
        <label className="form-check-label ms-2">
          <input type="checkbox" name="hideZeroStock" checked={filters.hideZeroStock} onChange={handleFilterChange} className="form-check-input" /> 在庫有
        </label>
        <button onClick={handleSearch} className="btn btn-primary">検索</button>
      </div>

      {/* Table */}
      <div className="table-responsive">
        <table className="table table-striped table-bordered table-hover mb-0">
          <thead>
            <tr>
              <th>製品/材料名</th>
              <th>倉庫</th>
              <th>場所</th>
              <th className="text-end">在庫数</th>
              <th className="text-end">引当在庫</th>
              <th className="text-end">利用可能数</th>
              <th>最終更新日時</th>
              <th className="text-center">操作</th>
            </tr>
          </thead>
          <tbody>{renderTableBody()}</tbody>
        </table>
      </div>

      {/* Pagination */}
      <div className="pagination-controls d-flex justify-content-center align-items-center mt-3">
        <button onClick={() => fetchInventory(pagination.previous)} className="btn btn-outline-primary" disabled={!pagination.previous}>前へ</button>
        <span className="mx-3">
          {pagination.count > 0 ? `ページ ${pagination.currentPage} / ${pagination.totalPages} (全 ${pagination.count} 件)` : ''}
        </span>
        <button onClick={() => fetchInventory(pagination.next)} className="btn btn-outline-primary" disabled={!pagination.next}>次へ</button>
      </div>

      {/* Modify Inventory Modal */}
      <Modal isOpen={modifyModal.isOpen} onClose={closeModifyModal}>
        <div className="inventory-modal-content">
            <h2>在庫修正</h2>
            <form onSubmit={handleModifySubmit}>
              <table className="table table-sm table-bordered mb-3">
                <tbody>
                  <tr>
                    <td style={{ width: '35%' }}><label className="mb-0">製品/材料名:</label></td>
                    <td><p className="mb-0">{modifyModal.item?.part_number}</p></td>
                  </tr>
                  <tr>
                    <td><label htmlFor="modal_warehouse_input" className="mb-0">倉庫:</label></td>
                    <td><input type="text" id="modal_warehouse_input" name="warehouse" value={modifyFormData.warehouse} onChange={handleModifyFormChange} className="form-control form-control-sm" /></td>
                  </tr>
                  <tr>
                    <td><label htmlFor="modal_location_input" className="mb-0">場所:</label></td>
                    <td><input type="text" id="modal_location_input" name="location" value={modifyFormData.location} onChange={handleModifyFormChange} className="form-control form-control-sm" /></td>
                  </tr>
                  <tr>
                    <td><label htmlFor="modal_quantity_input" className="mb-0">在庫数:</label></td>
                    <td><input type="number" id="modal_quantity_input" name="quantity" value={modifyFormData.quantity} onChange={handleModifyFormChange} className="form-control form-control-sm text-end" required /></td>
                  </tr>
                  <tr>
                    <td><label className="mb-0">引当在庫 (変更不可):</label></td>
                    <td><p className="mb-0 text-end" style={{ paddingRight: '0.5rem' }}>{modifyModal.item?.reserved}</p></td>
                  </tr>
                  <tr>
                    <td><label className="mb-0">利用可能数 (参考):</label></td>
                    <td><p className="mb-0 text-end" style={{ paddingRight: '0.5rem' }}>{modifyModal.item?.available_quantity}</p></td>
                  </tr>
                </tbody>
              </table>
              {modifyModal.error && <div className="alert alert-danger">{modifyModal.error}</div>}
              {modifyModal.success && <div className="alert alert-success">{modifyModal.success}</div>}
              <div className="mt-3 text-end">
                <button type="submit" className="btn btn-primary btn-sm">保存</button>
                <button type="button" className="btn btn-secondary btn-sm ms-2" onClick={closeModifyModal}>キャンセル</button>
              </div>
            </form>
        </div>
      </Modal>

      {/* Move Inventory Modal */}
      <Modal isOpen={moveModal.isOpen} onClose={closeMoveModal}>
        <div className="inventory-modal-content">
            <h2>在庫移動</h2>
            <form onSubmit={handleMoveSubmit}>
              <p><strong>品番:</strong> <span>{moveModal.item?.part_number}</span></p>
              <p><strong>移動元倉庫:</strong> <span>{moveModal.item?.warehouse}</span></p>
              <p><strong>移動元棚番:</strong> <span>{moveModal.item?.location}</span></p>
              <p><strong>現在数量:</strong> <span>{moveModal.item?.quantity}</span></p>
              <hr />
              <div className="mb-3">
                <label htmlFor="move_quantity_input" className="form-label">移動数量:</label>
                <input type="number" id="move_quantity_input" name="quantity_to_move" value={moveFormData.quantity_to_move} onChange={handleMoveFormChange} className="form-control form-control-sm" required min="1" max={moveModal.item?.quantity} />
              </div>
              <div className="mb-3">
                <label htmlFor="move_target_warehouse_input" className="form-label">移動先倉庫:</label>
                <input type="text" id="move_target_warehouse_input" name="target_warehouse" value={moveFormData.target_warehouse} onChange={handleMoveFormChange} className="form-control form-control-sm" required placeholder="例: 第二倉庫" />
              </div>
              <div className="mb-3">
                <label htmlFor="move_target_location_input" className="form-label">移動先棚番:</label>
                <input type="text" id="move_target_location_input" name="target_location" value={moveFormData.target_location} onChange={handleMoveFormChange} className="form-control form-control-sm" placeholder="例: B-02-01" />
              </div>
              {moveModal.error && <div className="alert alert-danger">{moveModal.error}</div>}
              {moveModal.success && <div className="alert alert-success">{moveModal.success}</div>}
              <div className="mt-3 text-end">
                <button type="submit" className="btn btn-success btn-sm">移動実行</button>
                <button type="button" className="btn btn-secondary btn-sm ms-2" onClick={closeMoveModal}>キャンセル</button>
              </div>
            </form>
        </div>
      </Modal>
    </div>
  );
};

export default InventoryInquiry;