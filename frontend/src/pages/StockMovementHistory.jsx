import React, { useState, useEffect, useCallback } from 'react';

// Constants from the Django template
const AVAILABLE_MOVEMENT_TYPES = [
    { key: 'incoming', label: '入庫', btnClass: 'btn-outline-primary', default_selected: true },
    { key: 'outgoing', label: '出庫', btnClass: 'btn-outline-secondary', default_selected: true },
    { key: 'used', label: '生産使用', btnClass: 'btn-outline-success', default_selected: true },
    { key: 'PRODUCTION_OUTPUT', label: '生産完了入庫', btnClass: 'btn-outline-info', default_selected: true },
    { key: 'PRODUCTION_REVERSAL', label: '生産完了取消', btnClass: 'btn-outline-warning', default_selected: true },
    { key: 'adjustment', label: '在庫調整', btnClass: 'btn-outline-danger', default_selected: true },
];

const getDefaultSelectedTypes = () => {
    const defaultTypes = new Set();
    AVAILABLE_MOVEMENT_TYPES.forEach(type => {
        if (type.default_selected) {
            defaultTypes.add(type.key);
        }
    });
    return defaultTypes;
};

const StockMovementHistory = () => {
    const [history, setHistory] = useState([]);
    const [pagination, setPagination] = useState({
        count: 0,
        num_pages: 1,
        current_page: 1,
        next: null,
        previous: null,
    });
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [searchCriteria, setSearchCriteria] = useState({
        search_part_number: '',
        search_warehouse: '',
        search_operator: '',
        search_movement_date_from: '',
        search_movement_date_to: '',
    });
    const [selectedTypes, setSelectedTypes] = useState(getDefaultSelectedTypes());
    
    // State to trigger fetch
    const [activeSearch, setActiveSearch] = useState({});
    const [currentPage, setCurrentPage] = useState(1);
    const [jumpPage, setJumpPage] = useState('1');

    const pageSize = 25;

    const fetchHistory = useCallback(async (page, params) => {
        setLoading(true);
        setError(null);
        const url = new URL(`${window.location.origin}/api/inventory/stock-movements/`);
        url.searchParams.append('page', page);
        url.searchParams.append('page_size', pageSize);

        Object.entries(params).forEach(([key, value]) => {
            if (value) {
                if (key === 'search_movement_type' && value.size > 0) {
                    value.forEach(type => {
                        url.searchParams.append(key, type);
                    });
                } else if (key !== 'search_movement_type' && value !== '') {
                    url.searchParams.append(key, value);
                }
            }
        });

        try {
            const response = await fetch(url);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const data = await response.json();
            setHistory(data.results || []);
            setPagination({
                count: data.count || 0,
                num_pages: data.num_pages || 1,
                current_page: data.current_page || 1,
                next: data.next,
                previous: data.previous,
            });
        } catch (e) {
            setError('データの読み込みに失敗しました。');
            console.error("Fetch error:", e);
        } finally {
            setLoading(false);
        }
    }, [pageSize]);

    useEffect(() => {
        fetchHistory(currentPage, activeSearch);
    }, [fetchHistory, currentPage, activeSearch]);

    useEffect(() => {
        setJumpPage(currentPage.toString());
    }, [currentPage]);

    const handleSearchChange = (e) => {
        const { name, value } = e.target;
        setSearchCriteria(prev => ({ ...prev, [name]: value }));
    };

    const handleTypeToggle = (typeKey) => {
        const newSelectedTypes = new Set(selectedTypes);
        if (newSelectedTypes.has(typeKey)) {
            newSelectedTypes.delete(typeKey);
        } else {
            newSelectedTypes.add(typeKey);
        }
        setSelectedTypes(newSelectedTypes);
        // Trigger search immediately
        setCurrentPage(1);
        setActiveSearch({ ...searchCriteria, search_movement_type: newSelectedTypes });
    };

    const handleSearch = () => {
        setCurrentPage(1);
        setActiveSearch({ ...searchCriteria, search_movement_type: selectedTypes });
    };

    const handleReset = () => {
        setSearchCriteria({
            search_part_number: '',
            search_warehouse: '',
            search_operator: '',
            search_movement_date_from: '',
            search_movement_date_to: '',
        });
        setSelectedTypes(getDefaultSelectedTypes());
        setCurrentPage(1);
        setActiveSearch({});
    };

    const handlePageChange = (page) => {
        if (page >= 1 && page <= pagination.num_pages && page !== currentPage) {
            setCurrentPage(page);
        }
    };

    const handleJumpPageChange = (e) => {
        setJumpPage(e.target.value);
    };

    const handleJumpPageGo = () => {
        const page = parseInt(jumpPage, 10);
        if (page >= 1 && page <= pagination.num_pages) {
            handlePageChange(page);
        } else {
            setJumpPage(currentPage.toString()); // Reset to current if invalid
        }
    };

    const handleJumpPageKeyPress = (e) => {
        if (e.key === 'Enter') {
            handleJumpPageGo();
        }
    };

    const renderHistoryCountInfo = () => {
        const { count, num_pages } = pagination;
        if (count === 0) {
            return '該当する履歴データはありません。';
        }
        const startItem = (currentPage - 1) * pageSize + 1;
        const endItem = Math.min(startItem + pageSize - 1, count);
        return `全 ${count} 件中 ${startItem} - ${endItem} 件を表示 (ページ ${currentPage} / ${num_pages})`;
    };

    const PaginationControls = () => {
        if (pagination.count <= pageSize) return null;

        const { num_pages } = pagination;
        const pageNumbers = [];
        const startPage = Math.max(1, currentPage - 3);
        const endPage = Math.min(num_pages, currentPage + 3);

        for (let i = startPage; i <= endPage; i++) {
            pageNumbers.push(i);
        }

        return (
            <div className="d-flex align-items-center">
                <nav aria-label="Page navigation">
                    <ul className="pagination mb-0">
                        <li className={`page-item ${!pagination.previous ? 'disabled' : ''}`}>
                            <button className="page-link" onClick={() => handlePageChange(pagination.previous)} aria-label="Previous">
                                <span aria-hidden="true">&laquo;</span>
                            </button>
                        </li>
                        {pageNumbers.map(pageNum => (
                            <li key={pageNum} className={`page-item ${currentPage === pageNum ? 'active' : ''}`}>
                                <button className="page-link" onClick={() => handlePageChange(pageNum)}>{pageNum}</button>
                            </li>
                        ))}
                        <li className={`page-item ${!pagination.next ? 'disabled' : ''}`}>
                            <button className="page-link" onClick={() => handlePageChange(pagination.next)} aria-label="Next">
                                <span aria-hidden="true">&raquo;</span>
                            </button>
                        </li>
                    </ul>
                </nav>
                {num_pages > 7 && (
                    <div className="d-flex align-items-center ms-3">
                        <span className="me-1 text-muted">ページ:</span>
                        <input
                            type="number"
                            min="1"
                            max={num_pages}
                            value={jumpPage}
                            onChange={handleJumpPageChange}
                            onKeyPress={handleJumpPageKeyPress}
                            className="form-control form-control-sm me-1"
                            style={{ width: '60px' }}
                        />
                        <button className="btn btn-secondary btn-sm" onClick={handleJumpPageGo}>移動</button>
                    </div>
                )}
            </div>
        );
    };

    return (
        <div id="schedule-container">
            <h2 className="mb-3">入出庫履歴検索</h2>
            <div id="search-criteria-area" className="mb-3 p-3 border rounded bg-light">
                {/* Row 1 */}
                <div className="row g-2 mb-2">
                    <div className="col-md-4">
                        <label htmlFor="search-part-number" className="form-label form-label-sm">品番:</label>
                        <input type="text" id="search-part-number" name="search_part_number" className="form-control form-control-sm" value={searchCriteria.search_part_number} onChange={handleSearchChange} />
                    </div>
                    <div className="col-md-4">
                        <label htmlFor="search-warehouse" className="form-label form-label-sm">倉庫:</label>
                        <input type="text" id="search-warehouse" name="search_warehouse" className="form-control form-control-sm" value={searchCriteria.search_warehouse} onChange={handleSearchChange} />
                    </div>
                    <div className="col-md-2">
                        <label htmlFor="search-movement-date-from" className="form-label form-label-sm">移動日 (From):</label>
                        <input type="date" id="search-movement-date-from" name="search_movement_date_from" className="form-control form-control-sm" value={searchCriteria.search_movement_date_from} onChange={handleSearchChange} />
                    </div>
                    <div className="col-md-2">
                        <label htmlFor="search-movement-date-to" className="form-label form-label-sm">移動日 (To):</label>
                        <input type="date" id="search-movement-date-to" name="search_movement_date_to" className="form-control form-control-sm" value={searchCriteria.search_movement_date_to} onChange={handleSearchChange} />
                    </div>
                </div>
                {/* Row 2 */}
                <div className="row g-2 mb-2">
                    <div className="col-md-4">
                        <label htmlFor="search-operator" className="form-label form-label-sm">記録者:</label>
                        <input type="text" id="search-operator" name="search_operator" className="form-control form-control-sm" value={searchCriteria.search_operator} onChange={handleSearchChange} />
                    </div>
                    <div className="col-md-2"></div>
                    <div className="col-md-3 align-self-end">
                        <button id="advanced-search-button" className="btn btn-primary btn-sm w-100" onClick={handleSearch}>検索</button>
                    </div>
                    <div className="col-md-3 align-self-end">
                        <button id="reset-search-button" type="button" className="btn btn-secondary btn-sm w-100" onClick={handleReset}>リセット</button>
                    </div>
                </div>
                {/* Row 3 */}
                <div className="row g-2">
                    <div className="col-md-12">
                        <label className="form-label form-label-sm">移動タイプ:</label>
                        <div id="movement-type-filters-container" className="d-flex flex-wrap gap-1">
                            {AVAILABLE_MOVEMENT_TYPES.map(type => {
                                const isChecked = selectedTypes.has(type.key);
                                const btnClass = isChecked ? type.btnClass.replace('btn-outline-', 'btn-') : type.btnClass;
                                return (
                                    <div key={type.key} className="form-check form-check-inline me-1 mb-1">
                                        <input
                                            type="checkbox"
                                            className="form-check-input visually-hidden"
                                            id={`movement-type-filter-${type.key}`}
                                            value={type.key}
                                            checked={isChecked}
                                            onChange={() => handleTypeToggle(type.key)}
                                        />
                                        <label className={`btn btn-sm ${btnClass}`} htmlFor={`movement-type-filter-${type.key}`}>
                                            {type.label}
                                        </label>
                                    </div>
                                );
                            })}
                        </div>
                    </div>
                </div>
            </div>

            <h2 className="mb-3">入出庫履歴</h2>
            <p id="history-count-info" className="text-muted">{renderHistoryCountInfo()}</p>
            
            <div className="table-responsive">
                <table id="schedule-table" className="table table-striped table-bordered table-hover table-sm">
                    <thead className="table-light">
                        <tr>
                            <th>移動日時</th>
                            <th>品番</th>
                            <th>倉庫</th>
                            <th>移動タイプ</th>
                            <th>数量</th>
                            <th>記録者</th>
                            <th>備考</th>
                            <th>参照ドキュメント</th>
                        </tr>
                    </thead>
                    <tbody>
                        {loading ? (
                            <tr><td colSpan="8" className="text-center">読み込み中...</td></tr>
                        ) : error ? (
                            <tr><td colSpan="8" className="text-center text-danger">{error}</td></tr>
                        ) : history.length > 0 ? (
                            history.map(item => (
                                <tr key={item.id}>
                                    <td>{item.movement_date}</td>
                                    <td>{item.part_number}</td>
                                    <td>{item.warehouse}</td>
                                    <td>{item.movement_type_display}</td>
                                    <td>{item.quantity}</td>
                                    <td>{item.operator_username}</td>
                                    <td>{item.description}</td>
                                    <td>{item.reference_document}</td>
                                </tr>
                            ))
                        ) : (
                            <tr><td colSpan="8" className="text-center">データがありません。</td></tr>
                        )}
                    </tbody>
                </table>
            </div>

            <div id="pagination-controls" className="d-flex justify-content-center mt-3">
                <PaginationControls />
            </div>
        </div>
    );
};

export default StockMovementHistory;