import React, { useState, useEffect, useCallback, useRef } from 'react';
import Sortable from 'sortablejs';
import { getCookie } from '../utils/cookies';

// This is a complex, single-file component to mimic the structure and functionality of master_creation.html.
// In a typical large-scale React application, this would be broken down into smaller, reusable components.

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

const DynamicField = ({ fieldName, config, value, onChange, error }) => {
    const inputId = `modal_id_${fieldName}`;

    if (config.widget_type === 'Select') {
        return (
            <select id={inputId} name={fieldName} value={value || ''} onChange={onChange} className={`form-control ${error ? 'is-invalid' : ''}`}>
                {(config.choices || []).map(([val, label]) => <option key={val} value={val}>{label}</option>)}
            </select>
        );
    }
    if (config.widget_type === 'CheckboxInput') {
        return (
            <div className="form-check">
                <input id={inputId} name={fieldName} type="checkbox" checked={!!value} onChange={onChange} className={`form-check-input ${error ? 'is-invalid' : ''}`} />
                <label htmlFor={inputId} className="form-check-label">{config.label}</label>
            </div>
        );
    }
    if (config.widget_type === 'Textarea') {
        return <textarea id={inputId} name={fieldName} value={value || ''} onChange={onChange} className={`form-control ${error ? 'is-invalid' : ''}`} rows="3" />;
    }
    const type = config.widget_type === 'NumberInput' ? 'number' : 'text';
    return (
        <input type={type} id={inputId} name={fieldName} value={value || ''} onChange={onChange} className={`form-control ${error ? 'is-invalid' : ''}`} step={type === 'number' ? 'any' : undefined}/>
    );
};

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
    const [mainForm, setMainForm] = useState(null);
    const [formsetForms, setFormsetForms] = useState([]);
    const [managementForm, setManagementForm] = useState({});
    const [emptyFormConfig, setEmptyFormConfig] = useState(null);
    
    const [formErrors, setFormErrors] = useState({});
    const [globalMessage, setGlobalMessage] = useState({ text: '', type: '' });

    const formsetTableBodyRef = useRef(null);
    const sortable = useRef(null);

    const fetchItems = useCallback(async () => {
        setLoading(true);
        try {
            // NOTE: The backend currently doesn't have a JSON API for listing items.
            // The following is a workaround to parse items from the HTML page,
            // mimicking how a user would see the initial data.
            // A dedicated API endpoint (e.g., GET /api/quality/inspection-items/) is the recommended approach.
            const response = await fetch('/quality/master_creation/list/');
            if (!response.ok) throw new Error('Network response was not ok');
            
            const htmlText = await response.text();
            const parser = new DOMParser();
            const doc = parser.parseFromString(htmlText, "text/html");
            const rows = Array.from(doc.querySelectorAll('tbody tr'));
            const parsedItems = rows.map(row => {
                const cells = row.querySelectorAll('td');
                if (cells.length < 6) return null; // Skip non-data rows
                return {
                    id: cells[5].querySelector('.edit-btn')?.dataset.id,
                    code: cells[0]?.textContent.trim(),
                    name: cells[1]?.textContent.trim(),
                    inspection_type_display: cells[2]?.textContent.trim(),
                    target_object_type_display: cells[3]?.textContent.trim(),
                    is_active: cells[4]?.textContent.trim() === 'はい',
                };
            }).filter(item => item && item.id); // Filter out empty/header rows
            setItems(parsedItems);

        } catch (e) {
            setListError(`一覧の読み込みに失敗しました: ${e.message}. Backend API might be missing.`);
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
                    setFormsetForms(currentForms => {
                        const newForms = [...currentForms];
                        const [movedItem] = newForms.splice(oldIndex, 1);
                        newForms.splice(newIndex, 0, movedItem);
                        return newForms.map((form, index) => ({
                            ...form,
                            order: { ...form.order, value: index + 1 }
                        }));
                    });
                },
            });
        }
        return () => {
            sortable.current?.destroy();
        };
    }, [isModalOpen]);

    const openModal = useCallback(async (id = null, name = '検査項目') => {
        setFormErrors({});
        setGlobalMessage({ text: '', type: '' });
        const isNew = id === null;
        // NOTE: Djangoのテンプレートタグ {% url 'quality:inspection_item_create' %} が解決するURLを
        // 下記に設定する必要があります。もしDjango側のURLが異なる場合は、こちらを修正してください。
        // 例: '/quality/inspection-item/create/'
        const url = isNew ? '/quality/master_creation/create/' : `/quality/master_creation/update/${id}/`;
        
        try {
            const response = await fetch(url, {
                credentials: 'include', // セッションクッキーをリクエストに含める
                headers: {
                    'Accept': 'application/json', // サーバーにJSON形式のレスポンスを要求する
                },
            });

            if (!response.ok) throw new Error(`サーバーからのデータ取得に失敗しました。 Status: ${response.status}`);
            const data = await response.json();
            
            // Example of handling errors returned as JSON with status 200
            if (data && data.errors) {
                const errorMessages = Object.values(data.errors).flat();
                throw new Error(errorMessages.join(' '));
            }
            
            setMainForm(data.form_data || {});
            setManagementForm(data.formset_data.management_form || {});
            setEmptyFormConfig(data.empty_form_fields_data || {});
            const initialForms = (data.formset_data.forms || []).map((form, index) => {
                const populatedForm = {};
                for(const key in form.fields) {
                    populatedForm[key] = { ...form.fields[key] };
                }
                // Add properties needed for client-side logic
                populatedForm.original_id = form.id;
                if (!populatedForm.order || populatedForm.order.value === null) {
                    populatedForm.order = { ...data.empty_form_fields_data.order, value: index + 1 };
                }
                return populatedForm;
            });
            setFormsetForms(initialForms);

            setEditingItemId(id);
            setModalMode(isNew ? 'new' : 'edit');
            setModalTitle(isNew ? '新規検査項目登録' : `${name} 変更`);
            setIsModalOpen(true);

        } catch (e) {
            let errorMessage = `モーダルの準備中にエラーが発生しました: ${e.message}`;
            // JSONパースエラーの場合、より具体的なメッセージを表示
            if (e instanceof SyntaxError) {
                errorMessage = 'サーバーから予期しない応答がありました。ログインしていないか、セッションがタイムアウトした可能性があります。ページを再読み込みしてください。';
            }
            console.error("モーダル表示中にエラーが発生しました:", e);
            setGlobalMessage({ text: errorMessage, type: 'danger'});
        }
    }, []);

    const handleMainFormChange = (e) => {
        const { name, value, type, checked } = e.target;
        const val = type === 'checkbox' ? checked : value;
        setMainForm(prev => ({ ...prev, [name]: { ...prev[name], value: val } }));
    };

    const handleFormsetChange = (e, index) => {
        const { name, value, type, checked } = e.target;
        const fieldName = name.split('-').pop();
        const val = type === 'checkbox' ? checked : value;
        setFormsetForms(prev => prev.map((form, i) => i === index ? { ...form, [fieldName]: { ...form[fieldName], value: val } } : form));
    };

    const addDetailRow = () => {
        const newRow = JSON.parse(JSON.stringify(emptyFormConfig)); // Deep copy
        newRow.order.value = formsetForms.length + 1;
        setFormsetForms(prev => [...prev, newRow]);
    };

    const toggleDeleteRow = (index) => {
        setFormsetForms(prev => prev.map((form, i) => {
            if (i === index) {
                const isMarkedForDelete = form.DELETE?.value;
                return { ...form, DELETE: { ...form.DELETE, value: !isMarkedForDelete } };
            }
            return form;
        }));
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setFormErrors({});
        setGlobalMessage({ text: '', type: '' });
        
        const formData = new FormData();
        formData.append('csrfmiddlewaretoken', getCookie('csrftoken'));

        for (const key in mainForm) {
            let value = mainForm[key].value;
            if (typeof value === 'boolean') value = value ? 'on' : '';
            formData.append(key, value ?? '');
        }

        const prefix = "measurement_details";
        formData.append(`${prefix}-TOTAL_FORMS`, formsetForms.length);
        formData.append(`${prefix}-INITIAL_FORMS`, managementForm.INITIAL_FORMS || formsetForms.filter(f => f.original_id).length);
        // Django formsets expect these, even if empty
        formData.append(`${prefix}-MIN_NUM_FORMS`, managementForm.MIN_NUM_FORMS || '0');
        formData.append(`${prefix}-MAX_NUM_FORMS`, managementForm.MAX_NUM_FORMS || '1000');

        formsetForms.forEach((form, index) => {
            for (const fieldName in form) {
                if (fieldName === 'original_id') continue;
                const key = `${prefix}-${index}-${fieldName}`;
                const value = form[fieldName]?.value;

                if (fieldName === 'id' && form.original_id) {
                    formData.append(`${prefix}-${index}-id`, form.original_id);
                } else if (fieldName === 'DELETE') {
                    if (value) formData.append(key, 'on');
                } else {
                    formData.append(key, value ?? '');
                }
            }
        });

        const url = modalMode === 'new' ? '/quality/master_creation/create/' : `/quality/master_creation/update/${editingItemId}/`;

        try {
            const response = await fetch(url, {
                method: 'POST',
                body: formData,
                credentials: 'include', // セッションクッキーをリクエストに含める
                headers: { 'Accept': 'application/json' }
            });
            const result = await response.json();

            if (result.success) {
                setGlobalMessage({ text: result.message || '保存しました。', type: 'success' });
                setTimeout(() => {
                    setIsModalOpen(false);
                    fetchItems();
                }, 1500);
            } else {
                setFormErrors(result.errors || {});
                setGlobalMessage({ text: result.message || '入力内容を確認してください。', type: 'danger' });
            }
        } catch (err) {
            setGlobalMessage({ text: `送信中にエラーが発生しました: ${err.message}`, type: 'danger' });
        }
    };
    
    const handleDelete = async (id, code) => {
        if (window.confirm(`検査項目「${code}」を本当に削除しますか？`)) {
            try {
                const response = await fetch(`/quality/master_creation/delete/${id}/`, {
                    method: 'POST',
                    headers: { 'X-CSRFToken': getCookie('csrftoken'), 'Accept': 'application/json' },
                });
                const data = await response.json();
                alert(data.message);
                if (data.success) fetchItems();
            } catch (err) {
                alert('削除中にエラーが発生しました。');
            }
        }
    };

    const renderFormField = (fieldName, config) => {
        const value = mainForm[fieldName]?.value;
        const error = formErrors[fieldName];
        if (!config) return null;
        if (config.widget_type === 'CheckboxInput') {
             return <div key={fieldName} className="form-group form-check align-self-end pb-3">{DynamicField({fieldName, config, value, onChange: handleMainFormChange, error })} <div className="invalid-feedback">{error}</div></div>;
        }
        return (
            <div key={fieldName} className="form-group">
                <label htmlFor={`modal_id_${fieldName}`}>{config.label}{config.is_required ? '*' : ''}</label>
                {DynamicField({fieldName, config, value, onChange: handleMainFormChange, error })}
                <div className="invalid-feedback">{error}</div>
            </div>
        );
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

            {isModalOpen && mainForm && (
                <div className="custom-modal-overlay">
                    <div className="custom-modal-content">
                        <h3>{modalTitle}</h3><hr />
                        <div className="custom-modal-form-body">
                            <form onSubmit={handleSubmit} noValidate>
                                {mainForm && <div id="mainInspectionItemFieldsContainer">{['code', 'name', 'inspection_type', 'target_object_type'].map(f => renderFormField(f, mainForm[f]))}</div>}
                                {mainForm && <div className="mt-3 row">{['description', 'is_active'].map(f => mainForm[f] && <div className="col-md-6" key={f}>{renderFormField(f, mainForm[f])}</div>)}</div>}
                                <hr />
                                <div id="measurementDetailsFormsetContainer">
                                    <div className="table-responsive">
                                        <table className="table table-sm table-bordered" style={{ tableLayout: 'fixed', width: '100%' }}>
                                            <thead className="thead-light">
                                                <tr>
                                                    <th style={{width: '30px'}}></th><th style={{width: '150px'}}>測定・判定名</th><th style={{width: '90px'}}>タイプ</th><th style={{width: '80px'}}>規格値(中心)</th><th style={{width: '80px'}}>規格上限</th><th style={{width: '80px'}}>規格下限</th><th style={{width: '60px'}}>単位</th><th style={{width: '100px'}}>期待結果(定性)</th><th style={{width: '60px'}}>順序</th><th style={{width: '60px'}}>削除</th>
                                                </tr>
                                            </thead>
                                            <tbody ref={formsetTableBodyRef}>
                                                {formsetForms.map((form, index) => {
                                                    const prefix = `measurement_details-${index}`;
                                                    const isQuantitative = form.measurement_type?.value === 'quantitative';
                                                    const isRowMarkedForDelete = form.DELETE?.value === true;
                                                    return (
                                                        <tr key={index} className="formset-row" style={{ display: isRowMarkedForDelete ? 'none' : 'table-row' }}>
                                                            <td className="drag-handle">☰</td>
                                                            <td><input type="text" value={form.name?.value || ''} onChange={e => handleFormsetChange(e, index)} name={`${prefix}-name`} className={`form-control form-control-sm ${formErrors[`${prefix}-name`] ? 'is-invalid' : ''}`} /><div className="invalid-feedback">{formErrors[`${prefix}-name`]}</div></td>
                                                            <td>
                                                                <select value={form.measurement_type?.value || ''} onChange={e => handleFormsetChange(e, index)} name={`${prefix}-measurement_type`} className={`form-control form-control-sm ${formErrors[`${prefix}-measurement_type`] ? 'is-invalid' : ''}`}>
                                                                    {(emptyFormConfig.measurement_type?.choices || []).map(([v, l]) => <option key={v} value={v}>{l}</option>)}
                                                                </select><div className="invalid-feedback">{formErrors[`${prefix}-measurement_type`]}</div>
                                                            </td>
                                                            {['specification_nominal', 'specification_upper_limit', 'specification_lower_limit', 'specification_unit'].map(f => (
                                                                <td key={f} style={{visibility: isQuantitative ? 'visible' : 'hidden'}}>
                                                                    <input type={f === 'specification_unit' ? 'text' : 'number'} step="any" value={isQuantitative ? form[f]?.value || '' : ''} onChange={e => handleFormsetChange(e, index)} name={`${prefix}-${f}`} className={`form-control form-control-sm ${formErrors[`${prefix}-${f}`] ? 'is-invalid' : ''}`} /><div className="invalid-feedback">{formErrors[`${prefix}-${f}`]}</div>
                                                                </td>
                                                            ))}
                                                            <td style={{visibility: !isQuantitative ? 'visible' : 'hidden'}}><input type="text" value={!isQuantitative ? form.expected_qualitative_result?.value || '' : ''} onChange={e => handleFormsetChange(e, index)} name={`${prefix}-expected_qualitative_result`} className={`form-control form-control-sm ${formErrors[`${prefix}-expected_qualitative_result`] ? 'is-invalid' : ''}`} /><div className="invalid-feedback">{formErrors[`${prefix}-expected_qualitative_result`]}</div></td>
                                                            <td><input type="number" value={form.order?.value || ''} onChange={e => handleFormsetChange(e, index)} name={`${prefix}-order`} className={`form-control form-control-sm ${formErrors[`${prefix}-order`] ? 'is-invalid' : ''}`} /><div className="invalid-feedback">{formErrors[`${prefix}-order`]}</div></td>
                                                            <td>{form.original_id && <input type="checkbox" className="form-check-input" checked={!!isRowMarkedForDelete} onChange={() => toggleDeleteRow(index)} title="削除" />}</td>
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
                                    <button type="button" className="btn btn-secondary" onClick={() => setIsModalOpen(false)}>閉じる</button>
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