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
    const [displaySettings, setDisplaySettings] = useState([]);
    const [searchFields, setSearchFields] = useState([]);

    const [searchCriteria, setSearchCriteria] = useState({
        part_number: '',
        warehouse: '',
        operator: '',
        movement_date_from: '',
        movement_date_to: '',
        reference_document: '',
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
        
        const dataUrl = new URL(`${window.location.origin}/api/inventory/stock-movements/`);
        dataUrl.searchParams.append('page', page);
        dataUrl.searchParams.append('page_size', pageSize);

        Object.entries(params).forEach(([key, value]) => {
            if (value) {
                if (key === 'movement_type' && value.size > 0) {
                    value.forEach(type => {
                        dataUrl.searchParams.append('search_movement_type', type);
                    });
                } else if (key !== 'movement_type' && value !== '') {
                    dataUrl.searchParams.append(`search_${key}`, value);
                }
            }
        });

        const settingsUrl = '/api/base/model-display-settings/?data_type=stock_movement';
        const fieldsUrl = '/api/base/model-fields/?data_type=stock_movement';

        try {
            const [settingsResponse, fieldsResponse, dataResponse] = await Promise.all([
                fetch(settingsUrl, { credentials: 'include' }),
                fetch(fieldsUrl, { credentials: 'include' }),
                fetch(dataUrl.toString(), { credentials: 'include' })
            ]);

            if (settingsResponse.ok && fieldsResponse.ok) {
                const settings = await settingsResponse.json();
                const fields = await fieldsResponse.json();
                const verboseNameMap = new Map(fields.map(f => [f.name, f.verbose_name]));

                const combinedSettings = settings.map(setting => ({
                    ...setting,
                    verbose_name: verboseNameMap.get(setting.model_field_name) || setting.model_field_name,
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
            }

            if (!dataResponse.ok) throw new Error(`HTTP error! status: ${dataResponse.status}`);
            const data = await dataResponse.json();
            setHistory(data.results || []);
            setPagination({
                count: data.count || 0,
                num_pages: data.total_pages || 1,
                current_page: data.current_page || 1,
                next: data.next,
                previous: data.previous,
            });
        } catch (e) {
            setError('データの読み込みに失敗しました。');
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
        setActiveSearch({ ...searchCriteria, movement_type: newSelectedTypes });
    };

    const handleSearch = () => {
        setCurrentPage(1);
        setActiveSearch({ ...searchCriteria, movement_type: selectedTypes });
    };

    const handleReset = () => {
        setSearchCriteria({
            part_number: '',
            warehouse: '',
            operator: '',
            movement_date_from: '',
            movement_date_to: '',
            reference_document: '',
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

    const renderTableHeaders = () => {
        if (loading || displaySettings.length === 0) {
            return (
                <tr>
                    <th>移動日時</th><th>品番</th><th>倉庫</th><th>移動タイプ</th>
                    <th>数量</th><th>記録者</th><th>備考</th><th>参照ドキュメント</th>
                </tr>
            );
        }
        return (
            <tr>
                {displaySettings.map(setting => (
                    <th key={setting.model_field_name}>
                        {setting.display_name || setting.verbose_name}
                    </th>
                ))}
            </tr>
        );
    };

    const renderTableBody = () => {
        const colSpan = displaySettings.length > 0 ? displaySettings.length : 8;
        if (loading) return <tr><td colSpan={colSpan} className="text-center">読み込み中...</td></tr>;
        if (error) return <tr><td colSpan={colSpan} className="text-center text-danger">{error}</td></tr>;
        if (history.length === 0) return <tr><td colSpan={colSpan} className="text-center">データがありません。</td></tr>;

        return history.map(item => (
            <tr key={item.id}>
                {displaySettings.map(setting => {
                    const fieldName = setting.model_field_name;
                    let cellValue;

                    switch (fieldName) {
                        case 'movement_type':
                            cellValue = item.movement_type_display;
                            break;
                        case 'operator':
                            cellValue = item.operator_username;
                            break;
                        default:
                            cellValue = item[fieldName];
                            break;
                    }

                    return <td key={fieldName}>{cellValue ?? ''}</td>;
                })}
            </tr>
        ));
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
                            <button className="page-link" onClick={() => handlePageChange(currentPage - 1)} aria-label="Previous">
                                <span aria-hidden="true">&laquo;</span>
                            </button>
                        </li>
                        {pageNumbers.map(pageNum => (
                            <li key={pageNum} className={`page-item ${currentPage === pageNum ? 'active' : ''}`}>
                                <button className="page-link" onClick={() => handlePageChange(pageNum)}>{pageNum}</button>
                            </li>
                        ))}
                        <li className={`page-item ${!pagination.next ? 'disabled' : ''}`}>
                            <button className="page-link" onClick={() => handlePageChange(currentPage + 1)} aria-label="Next">
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
                <div className="row g-2 mb-2">
                    {searchFields.map(field => (
                        <div className="col-md-3" key={field.model_field_name}>
                            <label htmlFor={`search-${field.model_field_name}`} className="form-label form-label-sm">{field.display_name || field.verbose_name}:</label>
                            <input
                                type={field.model_field_name.includes('date') ? 'date' : 'text'}
                                id={`search-${field.model_field_name}`}
                                name={field.model_field_name}
                                className="form-control form-control-sm"
                                value={searchCriteria[field.model_field_name] || ''}
                                onChange={handleSearchChange}
                                placeholder={`${field.display_name || field.verbose_name}で検索...`}
                            />
                        </div>
                    ))}
                </div>
                <div className="row g-2 mb-2 align-items-end">
                    <div className="col-md-auto ms-auto">
                        <button id="advanced-search-button" className="btn btn-primary btn-sm" onClick={handleSearch}>検索</button>
                        <button id="reset-search-button" type="button" className="btn btn-secondary btn-sm ms-2" onClick={handleReset}>リセット</button>
                    </div>
                </div>
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
                        {renderTableHeaders()}
                    </thead>
                    <tbody>{renderTableBody()}</tbody>
                </table>
            </div>

            <div id="pagination-controls" className="d-flex justify-content-center mt-3">
                <PaginationControls />
            </div>
        </div>
    );
};

export default StockMovementHistory;