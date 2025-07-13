import React, { useState, useEffect, useCallback } from 'react';
import { getCookie } from '../utils/cookies'; // Assuming this utility exists
import Modal from '../components/Modal'; // Assuming this component exists

const ProductionPlan = () => {
  // Main state
  const [plans, setPlans] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [pagination, setPagination] = useState({ count: 0, next: null, previous: null });
  const [pageInfo, setPageInfo] = useState('');

  // Filters state
  const initialFilters = {
    plan_name: '',
    product_code: '',
    status: '',
    parent_plan_ref: '',
    planned_start_from: '',
    planned_start_to: '',
  };
  const [filters, setFilters] = useState(initialFilters);

  // Modals state
  const [detailModal, setDetailModal] = useState({ isOpen: false, plan: null });
  const [allocateModal, setAllocateModal] = useState({ 
    isOpen: false, 
    plan: null, 
    requiredParts: [], 
    partsLoading: false, 
    partsError: null,
    allocationResult: null, // To show success/error message after allocation
  });

  const pageSize = 100;

  // Build search query from filters
  const buildSearchQuery = useCallback((pageUrl = null) => {
    if (pageUrl) {
      return pageUrl;
    }
    const params = new URLSearchParams();
    params.append('page_size', pageSize.toString());
    if (filters.plan_name) params.append('plan_name', filters.plan_name);
    if (filters.product_code) params.append('product_code', filters.product_code);
    if (filters.status) params.append('status', filters.status);
    if (filters.parent_plan_ref) params.append('production_plan_ref', filters.parent_plan_ref);
    if (filters.planned_start_from) params.append('planned_start_datetime_after', filters.planned_start_from);
    if (filters.planned_start_to) params.append('planned_start_datetime_before', filters.planned_start_to);
    
    return `/api/production/plans/?${params.toString()}`;
  }, [filters, pageSize]);

  // Fetch production plans
  const fetchProductionPlans = useCallback(async (pageUrl = null) => {
    setLoading(true);
    setError(null);
    const url = buildSearchQuery(pageUrl);

    try {
      const response = await fetch(url);
      if (!response.ok) {
        throw new Error(`Network response was not ok: ${response.statusText}`);
      }
      const data = await response.json();
      setPlans(data.results || []);
      setPagination({ count: data.count, next: data.next, previous: data.previous });

      // Update page info
      if (data.count > 0) {
        let currentPage = 1;
        if (data.next) {
          const nextPageUrl = new URL(data.next, window.location.origin);
          currentPage = parseInt(nextPageUrl.searchParams.get('page')) - 1;
        } else if (data.previous) {
          const prevPageUrl = new URL(data.previous, window.location.origin);
          currentPage = parseInt(prevPageUrl.searchParams.get('page')) + 1;
        } else if (data.results && data.results.length > 0) {
            currentPage = 1;
        }
        if (currentPage < 1 && data.count > 0) {
            currentPage = 1;
        }
        const totalPages = Math.ceil(data.count / pageSize);
        setPageInfo(`ページ ${currentPage} / ${totalPages} (全 ${data.count} 件)`);
      } else {
        setPageInfo('データがありません');
      }

    } catch (e) {
      setError('生産計画データの取得中にエラーが発生しました。');
      console.error('Fetch error:', e);
      setPlans([]);
      setPageInfo('エラー');
    } finally {
      setLoading(false);
    }
  }, [buildSearchQuery, pageSize]);

  // Initial fetch and fetch on filter change
  useEffect(() => {
    fetchProductionPlans();
  }, [fetchProductionPlans]);

  // Filter handlers
  const handleFilterChange = (e) => {
    const { name, value } = e.target;
    setFilters(prev => ({ ...prev, [name]: value }));
  };

  const handleSearch = (e) => {
    e.preventDefault();
    fetchProductionPlans();
  };

  const handleClearSearch = () => {
    setFilters(initialFilters);
  };

  // Date formatter
  const formatDate = (dateStr) => {
    if (!dateStr) return 'N/A';
    const options = { year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' };
    return new Date(dateStr).toLocaleString('ja-JP', options);
  };

  // --- Detail Modal Logic ---
  const openDetailModal = (plan) => setDetailModal({ isOpen: true, plan });
  const closeDetailModal = () => setDetailModal({ isOpen: false, plan: null });

  // --- Allocation Modal Logic ---
  const calculateDefaultAllocation = (requiredStr, inventoryStr, alreadyAllocatedStr) => {
    const requiredQty = parseFloat(requiredStr) || 0;
    const inventoryQty = parseInt(inventoryStr, 10) || 0;
    const alreadyAllocatedQty = parseFloat(alreadyAllocatedStr) || 0;
    const stillNeeded = Math.max(0, requiredQty - alreadyAllocatedQty);
    const defaultToAllocate = Math.min(stillNeeded, inventoryQty);
    return Math.max(0, defaultToAllocate);
  };

  const openAllocateModal = (plan) => {
    setAllocateModal({ isOpen: true, plan, requiredParts: [], partsLoading: true, partsError: null, allocationResult: null });
  };

  const closeAllocateModal = () => {
    setAllocateModal({ isOpen: false, plan: null, requiredParts: [], partsLoading: false, partsError: null, allocationResult: null });
  };

  useEffect(() => {
    if (allocateModal.isOpen && allocateModal.plan && !allocateModal.allocationResult) {
      const fetchRequiredParts = async () => {
        setAllocateModal(prev => ({ ...prev, partsLoading: true, partsError: null }));
        try {
          const response = await fetch(`/api/production/plans/${allocateModal.plan.id}/required-parts/`);
          if (!response.ok) {
            const errorData = await response.json().catch(() => null);
            const errorMessage = errorData?.detail || response.statusText || `サーバーエラー (${response.status})`;
            throw new Error(errorMessage);
          }
          const data = await response.json();
          const partsWithAllocation = data.map(part => ({
            ...part,
            quantity_to_allocate: calculateDefaultAllocation(part.required_quantity, part.inventory_quantity, part.already_allocated_quantity)
          }));
          setAllocateModal(prev => ({ ...prev, requiredParts: partsWithAllocation, partsLoading: false }));
        } catch (e) {
          setAllocateModal(prev => ({ ...prev, partsError: e.message, partsLoading: false }));
        }
      };
      fetchRequiredParts();
    }
  }, [allocateModal.isOpen, allocateModal.plan, allocateModal.allocationResult]);

  const handleAllocationQuantityChange = (partCode, value) => {
    setAllocateModal(prev => ({
      ...prev,
      requiredParts: prev.requiredParts.map(part => 
        part.part_code === partCode ? { ...part, quantity_to_allocate: value } : part
      )
    }));
  };

  const handleAllocationSubmit = async () => {
    const { plan, requiredParts } = allocateModal;
    if (!plan || !requiredParts) return;

    const allocationsData = requiredParts
      .filter(part => (parseFloat(part.quantity_to_allocate) || 0) > 0 && part.warehouse && part.warehouse !== 'N/A')
      .map(part => ({
        part_number: part.part_code,
        warehouse: part.warehouse,
        quantity_to_allocate: parseFloat(part.quantity_to_allocate)
      }));

    if (allocationsData.length === 0) {
      alert('引き当て対象の有効な部品がありません。');
      return;
    }

    const csrfToken = getCookie('csrftoken');
    try {
      const response = await fetch(`/api/production/plans/${plan.id}/allocate-materials/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken },
        body: JSON.stringify({ allocations: allocationsData })
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.error || data.detail || '引き当てに失敗しました。');
      setAllocateModal(prev => ({ ...prev, allocationResult: { type: 'success', data } }));
      try {
        const bc = new BroadcastChannel('allocation_results_channel');
        bc.postMessage({ type: 'allocationResult', data });
        bc.close();
      } catch (e) { console.error('Error broadcasting allocation result:', e); }
    } catch (e) {
      setAllocateModal(prev => ({ ...prev, allocationResult: { type: 'error', message: e.message } }));
    }
  };

  const formatDecimalQuantity = (value) => {
    const num = parseFloat(value);
    if (isNaN(num)) return value;
    return (num % 1 === 0) ? num.toFixed(0) : num.toString();
  };

  const renderTableBody = () => {
    if (loading) return <tr><td colSpan="9" className="text-center">読み込み中...</td></tr>;
    if (error) return <tr><td colSpan="9" className="text-center text-danger">{error}</td></tr>;
    if (plans.length === 0) return <tr><td colSpan="9" className="text-center">生産計画データがありません。</td></tr>;
    return plans.map(plan => (
      <tr key={plan.id}>
        <td>{plan.plan_name || 'N/A'}</td>
        <td>{plan.product_code || 'N/A'}</td>
        <td className="text-end">{plan.planned_quantity}</td>
        <td className="text-center">{formatDate(plan.planned_start_datetime)}</td>
        <td className="text-center">{formatDate(plan.planned_end_datetime)}</td>
        <td className="text-center">{plan.status || 'N/A'}</td>
        <td className="text-center">{plan.production_plan || 'N/A'}</td>
        <td className="text-center"><button className="btn btn-sm btn-info" onClick={() => openDetailModal(plan)}>詳細</button></td>
        <td className="text-center"><button className="btn btn-sm btn-warning" onClick={() => openAllocateModal(plan)}>材料引当</button></td>
      </tr>
    ));
  };

  const renderDetailModalContent = () => {
    const { plan } = detailModal;
    if (!plan) return null;
    const fullFormat = (d) => d ? new Date(d).toLocaleString('ja-JP') : 'N/A';
    return (
      <>
        <div className="d-flex justify-content-between align-items-center mb-3 border-bottom pb-2">
          <h5 className="mb-0">生産計画詳細</h5>
          <button type="button" className="btn-close" aria-label="Close" onClick={closeDetailModal}></button>
        </div>
        <dl className="row mb-3">
          <dt className="col-sm-4">計画名:</dt><dd className="col-sm-8">{plan.plan_name || 'N/A'}</dd>
          <dt className="col-sm-4">製品コード:</dt><dd className="col-sm-8">{plan.product_code || 'N/A'}</dd>
          <dt className="col-sm-4">計画数量:</dt><dd className="col-sm-8 text-end">{plan.planned_quantity}</dd>
          <dt className="col-sm-4">計画開始日時:</dt><dd className="col-sm-8">{fullFormat(plan.planned_start_datetime)}</dd>
          <dt className="col-sm-4">計画終了日時:</dt><dd className="col-sm-8">{fullFormat(plan.planned_end_datetime)}</dd>
          <dt className="col-sm-4">実績開始日時:</dt><dd className="col-sm-8">{fullFormat(plan.actual_start_datetime)}</dd>
          <dt className="col-sm-4">実績終了日時:</dt><dd className="col-sm-8">{fullFormat(plan.actual_end_datetime)}</dd>
          <dt className="col-sm-4">ステータス:</dt><dd className="col-sm-8">{plan.status || 'N/A'}</dd>
          <dt className="col-sm-4">親計画ID:</dt><dd className="col-sm-8">{plan.production_plan || 'N/A'}</dd>
          <dt className="col-sm-4">備考:</dt><dd className="col-sm-8">{plan.remarks || ''}</dd>
          <dt className="col-sm-4">作成日時:</dt><dd className="col-sm-8">{fullFormat(plan.created_at)}</dd>
          <dt className="col-sm-4">更新日時:</dt><dd className="col-sm-8">{fullFormat(plan.updated_at)}</dd>
        </dl>
        <div className="text-end mt-4"><button className="btn btn-secondary" onClick={closeDetailModal}>閉じる</button></div>
      </>
    );
  };

  const renderAllocateModalContent = () => {
    const { plan, requiredParts, partsLoading, partsError, allocationResult } = allocateModal;
    if (!plan) return null;
    if (allocationResult) {
      const { type, data, message } = allocationResult;
      return (
        <>
          <div className="d-flex justify-content-between align-items-center mb-3 border-bottom pb-2">
            <h5 className="mb-0">{type === 'success' ? '材料引き当て完了' : '材料引き当てエラー'}</h5>
            <button type="button" className="btn-close" aria-label="Close" onClick={closeAllocateModal}></button>
          </div>
          <div className={`alert alert-${type === 'success' ? 'success' : 'danger'}`}>
            {type === 'success' ? data.message || '材料の引き当てが完了しました。' : message}
          </div>
          {type === 'success' && data.allocations_summary && (
            <div className="border p-2 mb-3" style={{ maxHeight: '200px', overflowY: 'auto' }}>
              <table className="table table-sm table-bordered">
                <thead className="table-light"><tr><th>部品番号</th><th className="text-end">引当数量</th><th>ステータス</th></tr></thead>
                <tbody>{data.allocations_summary.map((item, i) => <tr key={i}><td>{item.part_number}</td><td className="text-end">{item.allocated_quantity}</td><td>{item.status}</td></tr>)}</tbody>
              </table>
            </div>
          )}
          <div className="text-end mt-4"><button className="btn btn-primary" onClick={() => { closeAllocateModal(); fetchProductionPlans(); }}>閉じる</button></div>
        </>
      );
    }
    return (
      <>
        <div className="d-flex justify-content-between align-items-center mb-3 border-bottom pb-2">
          <h5 className="mb-0">材料引き当て確認</h5>
          <button type="button" className="btn-close" aria-label="Close" onClick={closeAllocateModal}></button>
        </div>
        <dl className="row mb-2">
          <dt className="col-sm-3">計画名:</dt><dd className="col-sm-9">{plan.plan_name || 'N/A'}</dd>
          <dt className="col-sm-3">製品コード:</dt><dd className="col-sm-9">{plan.product_code || 'N/A'}</dd>
          <dt className="col-sm-3">計画数量:</dt><dd className="col-sm-9 text-end">{plan.planned_quantity}</dd>
        </dl>
        <h6 className="mt-3">必要部品一覧</h6>
        <div className="border p-2 mt-1 mb-3" style={{ maxHeight: '250px', overflowY: 'auto' }}>
          {partsLoading && <p>部品情報を読み込み中...</p>}
          {partsError && <p className="text-danger">{partsError}</p>}
          {!partsLoading && !partsError && (
            <table className="table table-sm table-bordered table-hover">
              <thead className="table-light">
                <tr><th>部品コード</th><th>部品名</th><th>倉庫</th><th className="text-end">総必要数</th><th className="text-end">引当済</th><th className="text-end">在庫</th><th className="text-end">引当数量</th><th>単位</th></tr>
              </thead>
              <tbody>
                {requiredParts.map(part => (
                  <tr key={part.part_code}>
                    <td>{part.part_code || 'N/A'}</td><td>{part.part_name || 'N/A'}</td><td>{part.warehouse || 'N/A'}</td>
                    <td className="text-end">{formatDecimalQuantity(part.required_quantity)}</td><td className="text-end">{formatDecimalQuantity(part.already_allocated_quantity)}</td><td className="text-end">{part.inventory_quantity}</td>
                    <td className="text-end"><input type="number" className="form-control form-control-sm text-end" value={part.quantity_to_allocate} onChange={(e) => handleAllocationQuantityChange(part.part_code, e.target.value)} min="0" style={{ width: '80px' }}/></td>
                    <td>{part.unit || 'N/A'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
        <div className="text-end mt-4">
          <button className="btn btn-primary" onClick={handleAllocationSubmit} disabled={partsLoading || partsError}>引き当て実行</button>
          <button className="btn btn-secondary ms-2" onClick={closeAllocateModal}>キャンセル</button>
        </div>
      </>
    );
  };

  return (
    <div className="container mt-4">
      <h2 className="text-center mb-4">生産計画検索</h2>
      <div className="card card-body bg-light mb-4">
        <form onSubmit={handleSearch}>
          <div className="row gx-2 gy-2 mb-3">
            <div className="col-md"><input type="text" name="plan_name" value={filters.plan_name} onChange={handleFilterChange} className="form-control form-control-sm" placeholder="計画名" /></div>
            <div className="col-md"><input type="text" name="product_code" value={filters.product_code} onChange={handleFilterChange} className="form-control form-control-sm" placeholder="製品コード" /></div>
            <div className="col-md">
              <select name="status" value={filters.status} onChange={handleFilterChange} className="form-select form-select-sm">
                <option value="">ステータス (すべて)</option><option value="PENDING">未着手</option><option value="IN_PROGRESS">進行中</option><option value="COMPLETED">完了</option><option value="ON_HOLD">保留</option><option value="CANCELLED">中止</option>
              </select>
            </div>
            <div className="col-md"><input type="text" name="parent_plan_ref" value={filters.parent_plan_ref} onChange={handleFilterChange} className="form-control form-control-sm" placeholder="親計画ID" /></div>
          </div>
          <div className="row gx-2 gy-2 align-items-end">
            <div className="col-md-auto"><label className="form-label mb-0 me-1">計画開始日:</label></div>
            <div className="col-md"><input type="date" name="planned_start_from" value={filters.planned_start_from} onChange={handleFilterChange} className="form-control form-control-sm" /></div>
            <div className="col-md-auto text-center px-1">～</div>
            <div className="col-md"><input type="date" name="planned_start_to" value={filters.planned_start_to} onChange={handleFilterChange} className="form-control form-control-sm" /></div>
            <div className="col-md-auto ms-md-2 mt-2 mt-md-0">
              <button type="submit" className="btn btn-success btn-sm">検索</button>
              <button type="button" onClick={handleClearSearch} className="btn btn-danger btn-sm ms-1">クリア</button>
            </div>
          </div>
        </form>
      </div>

      <div className="table-responsive">
        <table className="table table-striped table-hover table-bordered table-sm">
          <thead>
            <tr>
              <th>計画名</th><th>製品コード</th><th className="text-end">計画数量</th><th className="text-center">計画開始日時</th>
              <th className="text-center">計画終了日時</th><th className="text-center">ステータス</th><th className="text-center">親計画ID</th>
              <th className="text-center">詳細</th><th className="text-center">材料引当</th>
            </tr>
          </thead>
          <tbody>{renderTableBody()}</tbody>
        </table>
      </div>

      <div className="text-center mt-4">
        <button onClick={() => fetchProductionPlans(pagination.previous)} className="btn btn-outline-primary mx-1" disabled={!pagination.previous}>前へ</button>
        <span className="mx-2">{pageInfo}</span>
        <button onClick={() => fetchProductionPlans(pagination.next)} className="btn btn-outline-primary mx-1" disabled={!pagination.next}>次へ</button>
      </div>

      <Modal isOpen={detailModal.isOpen} onClose={closeDetailModal}>
        <div className="bg-white p-4 rounded-2 shadow-lg text-start" style={{ width: '90%', maxWidth: '900px' }}>{renderDetailModalContent()}</div>
      </Modal>

      <Modal isOpen={allocateModal.isOpen} onClose={closeAllocateModal}>
        <div className="bg-white p-4 rounded-2 shadow-lg text-start" style={{ width: '90%', maxWidth: '900px' }}>{renderAllocateModalContent()}</div>
      </Modal>
    </div>
  );
};

export default ProductionPlan;