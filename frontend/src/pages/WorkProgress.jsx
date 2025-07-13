import React, { useState, useEffect, useCallback } from 'react';
import { getCookie } from '../utils/cookies';
import Modal from '../components/Modal'; // Generic Modal component

// Constants for statuses, similar to the Django template
const AVAILABLE_STATUSES = [
    { key: 'PENDING', label: '未着手', btnClass: 'btn-secondary', btnOutlineClass: 'btn-outline-secondary', default_selected: true },
    { key: 'IN_PROGRESS', label: '進行中', btnClass: 'btn-info',     btnOutlineClass: 'btn-outline-info',    default_selected: true },
    { key: 'COMPLETED', label: '完了',    btnClass: 'btn-success',  btnOutlineClass: 'btn-outline-success', default_selected: false },
    { key: 'ON_HOLD', label: '保留',    btnClass: 'btn-warning',  btnOutlineClass: 'btn-outline-warning', default_selected: true },
    { key: 'CANCELLED', label: '中止',  btnClass: 'btn-danger',   btnOutlineClass: 'btn-outline-danger',  default_selected: false }
];

const getDefaultSelectedStatuses = () => {
    return new Set(AVAILABLE_STATUSES.filter(s => s.default_selected).map(s => s.key));
};

const WorkProgress = () => {
    // Data and loading states
    const [plans, setPlans] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    // Pagination states
    const [pagination, setPagination] = useState({ count: 0, next: null, previous: null });
    const [pageInfo, setPageInfo] = useState('');
    const pageSize = 10;

    // Filtering and sorting states
    const initialFilters = {
        plan_name: '',
        product_code: '',
        planned_start_after: '',
        planned_start_before: '',
    };
    const [filters, setFilters] = useState(initialFilters);
    const [statusFilters, setStatusFilters] = useState(getDefaultSelectedStatuses());
    const [sorting, setSorting] = useState({ field: 'planned_start_datetime', direction: 'desc' });

    // Modal states
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [selectedPlan, setSelectedPlan] = useState(null);
    const [modalQuantities, setModalQuantities] = useState({ actual: '', good: '', defective: '' });
    const [modalStatus, setModalStatus] = useState('');
    const [modalError, setModalError] = useState('');

    // API call logic
    const buildApiUrl = useCallback((pageUrl = null) => {
        if (pageUrl) {
            const url = new URL(pageUrl, window.location.origin);
            if (!url.searchParams.has('page_size')) {
                url.searchParams.set('page_size', pageSize.toString());
            }
            return url.toString();
        }

        const params = new URLSearchParams();
        params.append('page_size', pageSize.toString());
        
        // Sorting
        const sortOrderPrefix = sorting.direction === 'desc' ? '-' : '';
        params.append('ordering', `${sortOrderPrefix}${sorting.field}`);

        // Text and Date Filters
        if (filters.plan_name) params.append('plan_name', filters.plan_name);
        if (filters.product_code) params.append('product_code', filters.product_code);
        if (filters.planned_start_after) params.append('planned_start_datetime_after', filters.planned_start_after);
        if (filters.planned_start_before) params.append('planned_start_datetime_before', `${filters.planned_start_before}T23:59:59`);

        // Status Filters
        if (statusFilters.size > 0 && statusFilters.size < AVAILABLE_STATUSES.length) {
            params.append('status__in', Array.from(statusFilters).join(','));
        }

        return `/api/production/plans/?${params.toString()}`;
    }, [filters, statusFilters, sorting, pageSize]);

    const fetchProductionPlans = useCallback(async (pageUrl = null) => {
        setLoading(true);
        setError(null);

        if (statusFilters.size === 0) {
            setPlans([]);
            setPagination({ count: 0, next: null, previous: null });
            setPageInfo('表示するステータスが選択されていません。');
            setLoading(false);
            return;
        }

        const url = buildApiUrl(pageUrl);

        try {
            const response = await fetch(url);
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
            }
            const data = await response.json();
            setPlans(data.results || []);
            setPagination({ count: data.count, next: data.next, previous: data.previous });
            
            if (data.count > 0) {
                let currentPage = 1;
                const urlParams = new URL(url, window.location.origin).searchParams;
                const pageParam = urlParams.get('page');
                if (pageParam) {
                    currentPage = parseInt(pageParam, 10);
                } else if (data.next) {
                    const nextPageUrl = new URL(data.next);
                    currentPage = parseInt(nextPageUrl.searchParams.get('page')) - 1;
                } else if (data.previous) {
                    const prevPageUrl = new URL(data.previous);
                    currentPage = parseInt(prevPageUrl.searchParams.get('page')) + 1;
                }
                const totalPages = Math.ceil(data.count / pageSize);
                setPageInfo(`ページ ${currentPage} / ${totalPages} (全 ${data.count} 件)`);
            } else {
                setPageInfo('登録されている生産計画はありません。');
            }

        } catch (e) {
            setError(`データの読み込みに失敗しました: ${e.message}`);
            setPlans([]);
            setPageInfo('');
        } finally {
            setLoading(false);
        }
    }, [buildApiUrl, statusFilters, pageSize]);

    useEffect(() => {
        fetchProductionPlans();
    }, [fetchProductionPlans]);

    // Handlers
    const handleFilterChange = (e) => {
        const { name, value } = e.target;
        setFilters(prev => ({ ...prev, [name]: value }));
    };

    const handleStatusFilterChange = (statusKey) => {
        const newStatusFilters = new Set(statusFilters);
        if (newStatusFilters.has(statusKey)) {
            newStatusFilters.delete(statusKey);
        } else {
            newStatusFilters.add(statusKey);
        }
        setStatusFilters(newStatusFilters);
    };

    const handleSearch = () => {
        fetchProductionPlans();
    };

    const handleReset = () => {
        setFilters(initialFilters);
        setStatusFilters(getDefaultSelectedStatuses());
        setSorting({ field: 'planned_start_datetime', direction: 'desc' });
    };

    const handleSort = (field) => {
        const direction = (sorting.field === field && sorting.direction === 'asc') ? 'desc' : 'asc';
        setSorting({ field, direction });
    };

    const formatDate = (dateString) => {
        if (!dateString) return '';
        const date = new Date(dateString);
        return date.toLocaleDateString('ja-JP', { year: 'numeric', month: '2-digit', day: '2-digit' });
    };

    // Modal Logic
    const openModal = (plan) => {
        setSelectedPlan(plan);
        setModalStatus(plan.status);
        setModalError('');
        
        let quantities = { actual: '', good: '', defective: '' };
        if (plan.status === 'COMPLETED') {
            quantities = {
                actual: plan.planned_quantity.toString(),
                good: plan.planned_quantity.toString(),
                defective: '0'
            };
        }
        setModalQuantities(quantities);
        setIsModalOpen(true);
    };

    const closeModal = () => {
        setIsModalOpen(false);
        setSelectedPlan(null);
    };

    const handleQuantityChange = (e) => {
        const { name, value } = e.target;
        const newQuantities = { ...modalQuantities, [name]: value };

        const actual = parseInt(newQuantities.actual, 10) || 0;
        const defective = parseInt(newQuantities.defective, 10) || 0;
        newQuantities.good = Math.max(0, actual - defective).toString();
        
        setModalQuantities(newQuantities);
    };

    const handleProgressSubmit = async () => {
        setModalError('');
        if (!selectedPlan || !modalStatus) return;

        const payload = { status: modalStatus };

        if (modalStatus === 'COMPLETED') {
            const actual = parseInt(modalQuantities.actual, 10);
            const good = parseInt(modalQuantities.good, 10);
            const defective = parseInt(modalQuantities.defective, 10);

            if (isNaN(actual) || actual < 0) { setModalError('製作数量を正しく入力してください。'); return; }
            if (isNaN(good) || good < 0) { setModalError('OK数量を正しく入力してください。'); return; }
            if (isNaN(defective) || defective < 0) { setModalError('NG数量を正しく入力してください。'); return; }
            if (good + defective > actual) { setModalError('OK数量とNG数量の合計は、製作数量を超えることはできません。'); return; }
            
            payload.actual_quantity = actual;
            payload.good_quantity = good;
            payload.defective_quantity = defective;
        }

        try {
            const csrfToken = getCookie('csrftoken');
            const response = await fetch(`/api/production/plans/${selectedPlan.id}/update-progress/`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken },
                body: JSON.stringify(payload),
            });
            const data = await response.json();
            if (!response.ok) {
                throw new Error(data.error || data.detail || '進捗の登録に失敗しました。');
            }
            closeModal();
            fetchProductionPlans(); // Refresh the list
        } catch (e) {
            setModalError(e.message);
        }
    };

    // Render helpers
    const renderSortIndicator = (field) => {
        if (sorting.field !== field) return <span className="sort-indicator"></span>;
        return sorting.direction === 'asc' ? <span className="sort-indicator asc">▲</span> : <span className="sort-indicator desc">▼</span>;
    };

    const renderTableBody = () => {
        if (loading) return <tr><td colSpan="6" className="text-center">データを読み込み中です...</td></tr>;
        if (error) return <tr><td colSpan="6" className="text-center text-danger">{error}</td></tr>;
        if (plans.length === 0) return <tr><td colSpan="6" className="text-center">{pageInfo}</td></tr>;

        return plans.map(plan => {
            const statusInfo = AVAILABLE_STATUSES.find(s => s.key === plan.status);
            return (
                <tr key={plan.id}>
                    <td>{plan.plan_name}</td>
                    <td>{plan.product_code}</td>
                    <td className="text-end">{plan.planned_quantity}</td>
                    <td className="text-center">{formatDate(plan.planned_start_datetime)}</td>
                    <td className="text-center">
                        <span className={`btn btn-sm ${statusInfo?.btnClass || 'btn-secondary'}`} style={{ pointerEvents: 'none' }}>
                            {statusInfo?.label || plan.status}
                        </span>
                    </td>
                    <td className="text-center">
                        <button className="btn btn-sm btn-primary" onClick={() => openModal(plan)}>
                            進捗確認
                        </button>
                    </td>
                </tr>
            );
        });
    };

    return (
        <div className="container mt-4">
            <div className="d-flex flex-column flex-md-row align-items-md-center justify-content-md-between mb-3">
                <h2 className="mb-2 mb-md-0 me-md-3">作業進捗 - 生産計画一覧</h2>
                <div className="d-flex flex-wrap align-items-center">
                    <span className="me-2 fw-bold">ステータスフィルター:</span>
                    <div className="d-flex flex-wrap">
                        {AVAILABLE_STATUSES.map(statusInfo => {
                            const isChecked = statusFilters.has(statusInfo.key);
                            return (
                                <div key={statusInfo.key} className="form-check form-check-inline me-2 mb-1">
                                    <input
                                        type="checkbox"
                                        className="form-check-input visually-hidden"
                                        id={`status-filter-${statusInfo.key}`}
                                        value={statusInfo.key}
                                        checked={isChecked}
                                        onChange={() => handleStatusFilterChange(statusInfo.key)}
                                    />
                                    <label
                                        className={`btn btn-sm ${isChecked ? statusInfo.btnClass : statusInfo.btnOutlineClass}`}
                                        htmlFor={`status-filter-${statusInfo.key}`}
                                    >
                                        {statusInfo.label}
                                    </label>
                                </div>
                            );
                        })}
                    </div>
                </div>
            </div>

            {/* Search Form */}
            <div className="row mb-3 g-2 align-items-end">
                <div className="col-md">
                    <label htmlFor="searchPlanName" className="form-label">計画名</label>
                    <input type="text" id="searchPlanName" name="plan_name" value={filters.plan_name} onChange={handleFilterChange} className="form-control" placeholder="計画名..." />
                </div>
                <div className="col-md">
                    <label htmlFor="searchProductCode" className="form-label">製品コード</label>
                    <input type="text" id="searchProductCode" name="product_code" value={filters.product_code} onChange={handleFilterChange} className="form-control" placeholder="製品コード..." />
                </div>
                <div className="col-md">
                    <label htmlFor="searchPlannedStartAfter" className="form-label">計画開始日 (以降)</label>
                    <input type="date" id="searchPlannedStartAfter" name="planned_start_after" value={filters.planned_start_after} onChange={handleFilterChange} className="form-control" />
                </div>
                <div className="col-md">
                    <label htmlFor="searchPlannedStartBefore" className="form-label">計画開始日 (以前)</label>
                    <input type="date" id="searchPlannedStartBefore" name="planned_start_before" value={filters.planned_start_before} onChange={handleFilterChange} className="form-control" />
                </div>
                <div className="col-md-auto">
                    <button onClick={handleSearch} className="btn btn-primary w-100">検索</button>
                </div>
                <div className="col-md-auto mt-3 mt-md-0">
                    <button onClick={handleReset} className="btn btn-secondary w-100">リセット</button>
                </div>
            </div>

            <div className="table-responsive">
                <table className="table table-striped table-hover table-bordered">
                    <thead>
                        <tr>
                            <th scope="col" onClick={() => handleSort('plan_name')} style={{ cursor: 'pointer' }}>計画名 {renderSortIndicator('plan_name')}</th>
                            <th scope="col" onClick={() => handleSort('product_code')} style={{ cursor: 'pointer' }}>製品コード {renderSortIndicator('product_code')}</th>
                            <th scope="col" className="text-end" onClick={() => handleSort('planned_quantity')} style={{ cursor: 'pointer' }}>計画数量 {renderSortIndicator('planned_quantity')}</th>
                            <th scope="col" className="text-center" onClick={() => handleSort('planned_start_datetime')} style={{ cursor: 'pointer' }}>計画開始日 {renderSortIndicator('planned_start_datetime')}</th>
                            <th scope="col" className="text-center" onClick={() => handleSort('status')} style={{ cursor: 'pointer' }}>ステータス {renderSortIndicator('status')}</th>
                            <th scope="col" className="text-center">アクション</th>
                        </tr>
                    </thead>
                    <tbody>
                        {renderTableBody()}
                    </tbody>
                </table>
            </div>

            <div className="pagination-controls text-center mt-4">
                <button className="btn btn-outline-primary mx-1" onClick={() => fetchProductionPlans(pagination.previous)} disabled={!pagination.previous}>前へ</button>
                <span className="mx-2 align-middle">{pageInfo}</span>
                <button className="btn btn-outline-primary mx-1" onClick={() => fetchProductionPlans(pagination.next)} disabled={!pagination.next}>次へ</button>
            </div>

            {/* Progress Modal */}
            {selectedPlan && (
                <Modal isOpen={isModalOpen} onClose={closeModal}>
                    <div className="modal-header">
                        <h5 className="modal-title">作業進捗確認 - 計画ID: {selectedPlan.id}</h5>
                        <button type="button" className="btn-close" onClick={closeModal}></button>
                    </div>
                    <div className="modal-body">
                        <p><strong>計画名:</strong> {selectedPlan.plan_name}</p>
                        <p><strong>製品コード:</strong> {selectedPlan.product_code}</p>
                        <p><strong>計画数量:</strong> {selectedPlan.planned_quantity}</p>
                        <p><strong>計画開始日:</strong> {formatDate(selectedPlan.planned_start_datetime)}</p>
                        <p><strong>現在のステータス:</strong> {AVAILABLE_STATUSES.find(s => s.key === selectedPlan.status)?.label}</p>
                        <hr />
                        <form onSubmit={(e) => e.preventDefault()}>
                            <div className="mb-3">
                                <label className="form-label">ステータス変更</label>
                                <div>
                                    {AVAILABLE_STATUSES.map(statusInfo => (
                                        <button
                                            key={statusInfo.key}
                                            type="button"
                                            className={`btn btn-sm me-1 mb-1 ${modalStatus === statusInfo.key ? statusInfo.btnClass : statusInfo.btnOutlineClass}`}
                                            onClick={() => setModalStatus(statusInfo.key)}
                                        >
                                            {statusInfo.label}
                                        </button>
                                    ))}
                                </div>
                            </div>

                            {modalStatus === 'COMPLETED' && (
                                <div>
                                    <h5>進捗数量入力</h5>
                                    <div className="mb-3">
                                        <label htmlFor="modalActualQuantity" className="form-label">製作数量</label>
                                        <input type="number" className="form-control" id="modalActualQuantity" name="actual" value={modalQuantities.actual} onChange={handleQuantityChange} min="0" />
                                    </div>
                                    <div className="mb-3">
                                        <label htmlFor="modalDefectiveQuantity" className="form-label">NG数量</label>
                                        <input type="number" className="form-control" id="modalDefectiveQuantity" name="defective" value={modalQuantities.defective} onChange={handleQuantityChange} min="0" />
                                    </div>
                                    <div className="mb-3">
                                        <label htmlFor="modalGoodQuantity" className="form-label">OK数量</label>
                                        <input type="number" className="form-control" id="modalGoodQuantity" name="good" value={modalQuantities.good} readOnly />
                                    </div>
                                </div>
                            )}
                            {modalError && <div className="alert alert-danger mt-2">{modalError}</div>}
                        </form>
                    </div>
                    <div className="modal-footer">
                        <button type="button" className="btn btn-secondary" onClick={closeModal}>閉じる</button>
                        <button type="button" className="btn btn-primary" onClick={handleProgressSubmit}>進捗を登録</button>
                    </div>
                </Modal>
            )}
        </div>
    );
};

export default WorkProgress;