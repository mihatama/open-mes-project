import React, { useState, useEffect, useCallback, useRef } from 'react';
import Sortable from 'sortablejs';
import { getCookie } from '../utils/cookies';

const modalStyles = `
.custom-modal-overlay {
    position: fixed; top: 0; left: 0; width: 100%; height: 100%;
    background-color: rgba(0, 0, 0, 0.6);
    display: flex; justify-content: center; align-items: center; z-index: 1050;
}
.custom-modal-content {
    background-color: white; padding: 25px; border-radius: 8px;
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
    width: 90%; max-width: 1140px; text-align: left;
    display: flex; flex-direction: column; max-height: 95vh;
}
.custom-modal-content h3 { margin-top: 0; margin-bottom: 15px; color: #333; font-size: 1.75rem; }
.custom-modal-form-body { overflow-y: auto; flex-grow: 1; padding: 5px; }
.custom-modal-actions {
    margin-top: 20px; text-align: right; border-top: 1px solid #dee2e6; padding-top: 15px;
}
.invalid-feedback { display: none; width: 100%; margin-top: .25rem; font-size: .875em; color: #dc3545; }
.is-invalid ~ .invalid-feedback { display: block; }
#mainInspectionItemFieldsContainer {
    display: flex; flex-wrap: nowrap; gap: 1rem; overflow-x: auto; padding-bottom: 1rem;
}
#mainInspectionItemFieldsContainer .form-group { flex: 0 0 auto; min-width: 200px; }
.drag-handle { cursor: move; text-align: center; vertical-align: middle; }
.formset-row .form-check-input { margin-left: auto; margin-right: auto; display: block; }
`;

// Constants for select field choices
const INSPECTION_TYPE_CHOICES = [
    ['acceptance', '受入検査'], ['in_process', '工程内検査'], ['final', '最終検査'],
    ['shipping', '出荷検査'], ['patrol', '巡回検査'],
];
const TARGET_OBJECT_CHOICES = [
    ['raw_material', '原材料'], ['component', '部品'], ['wip', '仕掛品'],
    ['finished_good', '完成品'], ['equipment', '設備'], ['process', '工程'],
];
const MEASUREMENT_TYPE_CHOICES = [
    ['quantitative', '定量測定'], ['qualitative', '定性判定'],
];

const QualityMasterCreation = () => {
    const [items, setItems] = useState([]);
    const [loading, setLoading] = useState(true);
    const [listError, setListError] = useState(null);

    // Modal State
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [modalMode, setModalMode] = useState('new'); // 'new' or 'edit'
    const [editingItemId, setEditingItemId] = useState(null);
    const [modalTitle, setModalTitle] = useState('');

    // Form State
    const [currentItem, setCurrentItem] = useState(null);
    const [measurementDetails, setMeasurementDetails] = useState([]);

    const [formErrors, setFormErrors] = useState({});
    const [globalMessage, setGlobalMessage] = useState({ text: '', type: '' });

    const formsetTableBodyRef = useRef(null);
    const sortable = useRef(null);

    const fetchItems = useCallback(async () => {
        setLoading(true);
        setListError(null);
        try {
            const response = await fetch('/api/quality/inspection-items/');
            if (!response.ok) throw new Error('Network response was not ok');
            const data = await response.json();
            if (data.status === 'success') {
                setItems(data.data);
            } else {
                throw new Error(data.message || 'Failed to fetch items');
            }
        } catch (e) {
            setListError(`一覧の読み込みに失敗しました: ${e.message}`);
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        fetchItems();
    }, [fetchItems]);

    useEffect(() => {
        if (isModalOpen && formsetTableBodyRef.current) {
            sortable.current = Sortable.create(formsetTableBodyRef.current, {
                handle: '.drag-handle',
                animation: 150,
                onEnd: (evt) => {
                    const { oldIndex, newIndex } = evt;
                    setMeasurementDetails(currentDetails => {
                        const newDetails = [...currentDetails];
                        const [movedItem] = newDetails.splice(oldIndex, 1);
                        newDetails.splice(newIndex, 0, movedItem);
                        return newDetails;
                    });
                },
            });
        }
        return () => {
            sortable.current?.destroy();
        };
    }, [isModalOpen, measurementDetails]);

    const openModal = useCallback(async (id = null, name = '検査項目') => {
        setFormErrors({});
        setGlobalMessage({ text: '', type: '' });
        const isNew = id === null;
        setModalMode(isNew ? 'new' : 'edit');
        setEditingItemId(id);

        if (isNew) {
            setModalTitle(isNew ? '新規検査項目登録' : `${name} 変更`);
            setCurrentItem({
                code: '', name: '', description: '',
                inspection_type: 'acceptance',
                target_object_type: 'raw_material',
                is_active: true,
            });
            setMeasurementDetails([]);
            setIsModalOpen(true);
        } else {
            setModalTitle(`${name} 変更`);
            try {
                const response = await fetch(`/api/quality/inspection-items/${id}/`);
                if (!response.ok) throw new Error(`サーバーが ${response.status} で応答しました`);
                const result = await response.json();
                if (result.status === 'success') {
                    const { measurement_details, ...itemData } = result.data;
                    setCurrentItem(itemData);
                    setMeasurementDetails(measurement_details || []);
                    setIsModalOpen(true);
                } else {
                    throw new Error(result.message || '項目データの読み込みに失敗しました');
                }
            } catch (e) {
                setGlobalMessage({ text: `データ読み込みエラー: ${e.message}`, type: 'danger' });
            }
        }
    }, []);

    const handleMainFormChange = (e) => {
        const { name, value, type, checked } = e.target;
        const val = type === 'checkbox' ? checked : value;
        setCurrentItem(prev => ({ ...prev, [name]: val }));
    };

    const handleDetailChange = (e, index) => {
        const { name, value, type } = e.target;
        setMeasurementDetails(prev => prev.map((detail, i) =>
            i === index ? { ...detail, [name]: type === 'number' ? (value === '' ? null : Number(value)) : value } : detail
        ));
    };

    const addDetailRow = () => {
        const newRow = {
            id: null, name: '', measurement_type: 'qualitative',
            specification_nominal: null, specification_upper_limit: null, specification_lower_limit: null,
            specification_unit: '', expected_qualitative_result: '',
        };
        setMeasurementDetails(prev => [...prev, newRow]);
    };

    const removeDetailRow = (index) => {
        setMeasurementDetails(prev => prev.filter((_, i) => i !== index));
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setFormErrors({});
        setGlobalMessage({ text: '', type: '' });

        const orderedDetails = measurementDetails.map((detail, index) => ({
            ...detail,
            order: index + 1,
        }));

        const payload = { ...currentItem, measurement_details: orderedDetails };

        const url = modalMode === 'new' ? '/api/quality/inspection-items/' : `/api/quality/inspection-items/${editingItemId}/`;
        const method = modalMode === 'new' ? 'POST' : 'PUT';

        try {
            const response = await fetch(url, {
                method: method,
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken'),
                },
                body: JSON.stringify(payload),
            });
            const result = await response.json();

            if (response.ok && result.status === 'success') {
                setGlobalMessage({ text: result.message, type: 'success' });
                setTimeout(() => {
                    setIsModalOpen(false);
                    fetchItems();
                }, 1500);
            } else {
                const errors = result.data || result;
                const flatErrors = {};
                if (errors.measurement_details && Array.isArray(errors.measurement_details)) {
                    errors.measurement_details.forEach((detailError, index) => {
                        if (detailError) {
                            for (const [field, messages] of Object.entries(detailError)) {
                                flatErrors[`measurement_details-${index}-${field}`] = messages.join(' ');
                            }
                        }
                    });
                    delete errors.measurement_details;
                }
                setFormErrors({ ...errors, ...flatErrors });
                setGlobalMessage({ text: result.message || '入力内容を確認してください。', type: 'danger' });
            }
        } catch (err) {
            setGlobalMessage({ text: `送信中にエラーが発生しました: ${err.message}`, type: 'danger' });
        }
    };

    const handleDelete = async (id, code) => {
        if (window.confirm(`検査項目「${code}」を本当に削除しますか？`)) {
            try {
                const response = await fetch(`/api/quality/inspection-items/${id}/`, {
                    method: 'DELETE',
                    headers: { 'X-CSRFToken': getCookie('csrftoken'), 'Accept': 'application/json' },
                });
                const data = await response.json();
                alert(data.message);
                if (response.ok && data.status === 'success') fetchItems();
            } catch (err) {
                alert('削除中にエラーが発生しました。');
            }
        }
    };

    if (loading) return <div>読み込み中...</div>;
    if (listError) return <div className="alert alert-danger">{listError}</div>;

    return (
        <>
            <style>{modalStyles}</style>
            <div className="container-fluid mt-4">
                <h4>検査項目マスター管理</h4>
                <button type="button" className="btn btn-primary mb-3" onClick={() => openModal(null)}>
                    <i className="fas fa-plus"></i> 新規登録
                </button>
                <div className="table-responsive">
                    <table className="table table-striped table-bordered table-hover">
                        <thead className="thead-light">
                            <tr>
                                <th>コード</th><th>検査項目名</th><th>検査種別</th><th>対象物タイプ</th><th>有効</th><th style={{ width: "150px" }}>操作</th>
                            </tr>
                        </thead>
                        <tbody>
                            {items.length > 0 ? items.map(item => (
                                <tr key={item.id}>
                                    <td>{item.code}</td><td>{item.name}</td><td>{item.inspection_type_display}</td><td>{item.target_object_type_display}</td>
                                    <td>{item.is_active ? <span className="badge badge-success">はい</span> : <span className="badge badge-secondary">いいえ</span>}</td>
                                    <td>
                                        <button type="button" className="btn btn-sm btn-info" onClick={() => openModal(item.id, item.name)}><i className="fas fa-edit"></i> 変更</button>
                                        <button type="button" className="btn btn-sm btn-danger ml-2" onClick={() => handleDelete(item.id, item.code)}><i className="fas fa-trash-alt"></i> 削除</button>
                                    </td>
                                </tr>
                            )) : (
                                <tr><td colSpan="6" className="text-center">登録されている検査項目はありません。</td></tr>
                            )}
                        </tbody>
                    </table>
                </div>
            </div>

            {isModalOpen && currentItem && (
                <div className="custom-modal-overlay">
                    <div className="custom-modal-content">
                        <h3>{modalTitle}</h3><hr />
                        <div className="custom-modal-form-body">
                            <form onSubmit={handleSubmit} noValidate>
                                <div id="mainInspectionItemFieldsContainer">
                                    <div className="form-group"><label htmlFor="modal_id_code">検査項目コード*</label><input type="text" id="modal_id_code" name="code" value={currentItem.code} onChange={handleMainFormChange} className={`form-control ${formErrors.code ? 'is-invalid' : ''}`} /><div className="invalid-feedback">{formErrors.code}</div></div>
                                    <div className="form-group"><label htmlFor="modal_id_name">検査項目名*</label><input type="text" id="modal_id_name" name="name" value={currentItem.name} onChange={handleMainFormChange} className={`form-control ${formErrors.name ? 'is-invalid' : ''}`} /><div className="invalid-feedback">{formErrors.name}</div></div>
                                    <div className="form-group"><label htmlFor="modal_id_inspection_type">検査種別*</label><select id="modal_id_inspection_type" name="inspection_type" value={currentItem.inspection_type} onChange={handleMainFormChange} className={`form-control ${formErrors.inspection_type ? 'is-invalid' : ''}`}>{INSPECTION_TYPE_CHOICES.map(([v, l]) => <option key={v} value={v}>{l}</option>)}</select><div className="invalid-feedback">{formErrors.inspection_type}</div></div>
                                    <div className="form-group"><label htmlFor="modal_id_target_object_type">対象物タイプ*</label><select id="modal_id_target_object_type" name="target_object_type" value={currentItem.target_object_type} onChange={handleMainFormChange} className={`form-control ${formErrors.target_object_type ? 'is-invalid' : ''}`}>{TARGET_OBJECT_CHOICES.map(([v, l]) => <option key={v} value={v}>{l}</option>)}</select><div className="invalid-feedback">{formErrors.target_object_type}</div></div>
                                </div>
                                <div className="mt-3 row">
                                    <div className="col-md-6"><div className="form-group"><label htmlFor="modal_id_description">説明</label><textarea id="modal_id_description" name="description" value={currentItem.description || ''} onChange={handleMainFormChange} className={`form-control ${formErrors.description ? 'is-invalid' : ''}`} rows="3" /><div className="invalid-feedback">{formErrors.description}</div></div></div>
                                    <div className="col-md-6"><div className="form-group form-check align-self-end pb-3"><input id="modal_id_is_active" name="is_active" type="checkbox" checked={currentItem.is_active} onChange={handleMainFormChange} className={`form-check-input ${formErrors.is_active ? 'is-invalid' : ''}`} /><label htmlFor="modal_id_is_active" className="form-check-label">有効フラグ</label><div className="invalid-feedback">{formErrors.is_active}</div></div></div>
                                </div>
                                <hr />
                                <div id="measurementDetailsFormsetContainer">
                                    <h5>測定・判定詳細</h5>
                                    <div className="table-responsive">
                                        <table className="table table-sm table-bordered" style={{ tableLayout: 'fixed', width: '100%' }}>
                                            <thead className="thead-light">
                                                <tr>
                                                    <th style={{width: '30px'}}></th><th style={{width: '150px'}}>測定・判定名*</th><th style={{width: '90px'}}>タイプ*</th><th style={{width: '80px'}}>規格値(中心)</th><th style={{width: '80px'}}>規格上限</th><th style={{width: '80px'}}>規格下限</th><th style={{width: '60px'}}>単位</th><th style={{width: '100px'}}>期待結果(定性)</th><th style={{width: '60px'}}>削除</th>
                                                </tr>
                                            </thead>
                                            <tbody ref={formsetTableBodyRef}>
                                                {measurementDetails.map((detail, index) => {
                                                    const prefix = `measurement_details-${index}`;
                                                    const isQuantitative = detail.measurement_type === 'quantitative';
                                                    return (
                                                        <tr key={index} className="formset-row">
                                                            <td className="drag-handle">☰</td>
                                                            <td><input type="text" value={detail.name || ''} onChange={e => handleDetailChange(e, index)} name="name" className={`form-control form-control-sm ${formErrors[`${prefix}-name`] ? 'is-invalid' : ''}`} /><div className="invalid-feedback">{formErrors[`${prefix}-name`]}</div></td>
                                                            <td><select value={detail.measurement_type || ''} onChange={e => handleDetailChange(e, index)} name="measurement_type" className={`form-control form-control-sm ${formErrors[`${prefix}-measurement_type`] ? 'is-invalid' : ''}`}>{MEASUREMENT_TYPE_CHOICES.map(([v, l]) => <option key={v} value={v}>{l}</option>)}</select><div className="invalid-feedback">{formErrors[`${prefix}-measurement_type`]}</div></td>
                                                            {['specification_nominal', 'specification_upper_limit', 'specification_lower_limit'].map(f => (<td key={f} style={{visibility: isQuantitative ? 'visible' : 'hidden'}}><input type="number" step="any" value={isQuantitative ? detail[f] ?? '' : ''} onChange={e => handleDetailChange(e, index)} name={f} className={`form-control form-control-sm ${formErrors[`${prefix}-${f}`] ? 'is-invalid' : ''}`} /><div className="invalid-feedback">{formErrors[`${prefix}-${f}`]}</div></td>))}
                                                            <td style={{visibility: isQuantitative ? 'visible' : 'hidden'}}><input type="text" value={isQuantitative ? detail.specification_unit || '' : ''} onChange={e => handleDetailChange(e, index)} name="specification_unit" className={`form-control form-control-sm ${formErrors[`${prefix}-specification_unit`] ? 'is-invalid' : ''}`} /><div className="invalid-feedback">{formErrors[`${prefix}-specification_unit`]}</div></td>
                                                            <td style={{visibility: !isQuantitative ? 'visible' : 'hidden'}}><input type="text" value={!isQuantitative ? detail.expected_qualitative_result || '' : ''} onChange={e => handleDetailChange(e, index)} name="expected_qualitative_result" className={`form-control form-control-sm ${formErrors[`${prefix}-expected_qualitative_result`] ? 'is-invalid' : ''}`} /><div className="invalid-feedback">{formErrors[`${prefix}-expected_qualitative_result`]}</div></td>
                                                            <td><button type="button" className="btn btn-sm btn-danger" onClick={() => removeDetailRow(index)} title="行を削除"><i className="fas fa-trash-alt"></i></button></td>
                                                        </tr>
                                                    );
                                                })}
                                            </tbody>
                                        </table>
                                    </div>
                                    <button type="button" onClick={addDetailRow} className="btn btn-sm btn-success mb-2"><i className="fas fa-plus"></i> 詳細追加</button>
                                </div>

                                {globalMessage.text && <div className={`alert alert-${globalMessage.type} mt-3`}>{globalMessage.text}</div>}

                                <div className="custom-modal-actions">
                                    <button type="submit" className="btn btn-primary">保存</button>
                                    <button type="button" className="btn btn-secondary ml-2" onClick={() => setIsModalOpen(false)}>閉じる</button>
                                </div>
                            </form>
                        </div>
                    </div>
                </div>
            )}
        </>
    );
};

export default QualityMasterCreation;