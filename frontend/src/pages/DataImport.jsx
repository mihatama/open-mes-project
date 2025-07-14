import React, { useState, useEffect, useCallback } from 'react';
import { Container, Row, Col, Card, Button, Modal, Form, Table, Spinner, Alert } from 'react-bootstrap';
import 'bootstrap/dist/css/bootstrap.min.css';
import { useDropzone } from 'react-dropzone';

// Helper to get CSRF token from cookies
const getCsrfToken = () => {
    const token = document.cookie.split('; ')
        .find(row => row.startsWith('csrftoken='))
        ?.split('=')[1];
    return token || '';
};

// Placeholder for form components. In a real app, these would be more complex.
const GenericForm = ({ fields, formData, setFormData }) => (
    <Form>
        {fields.map(field => (
            <Form.Group className="mb-3" controlId={field.name} key={field.name}>
                <Form.Label>{field.label}</Form.Label>
                {field.type === 'select' ? (
                    <Form.Select
                        name={field.name}
                        value={formData[field.name] || ''}
                        onChange={e => setFormData(prev => ({ ...prev, [field.name]: e.target.value }))}
                    >
                        <option value="">選択してください</option>
                        {field.options.map(option => (
                            <option key={option.value} value={option.value}>
                                {option.label}
                            </option>
                        ))}
                    </Form.Select>
                ) : (
                    <Form.Control
                        type={field.type || 'text'}
                        placeholder={`${field.label}を入力`}
                        name={field.name}
                        value={formData[field.name] || ''}
                        onChange={e => setFormData(prev => ({ ...prev, [field.name]: e.target.value }))}
                    />
                )}
            </Form.Group>
        ))}
    </Form>
);

const getFormFields = (type) => {
    // This function would return form field configurations based on the type.
    // For brevity, we'll use a simplified version.
    const allFields = {
        item: [
            { name: 'code', label: 'コード' },
            { name: 'name', label: '品番名' },
            { name: 'item_type', label: '品目タイプ', type: 'select', options: [
                { value: 'product', label: '製品' }, { value: 'material', label: '材料' }
            ]},
            { name: 'unit', label: '単位' },
            { name: 'default_warehouse', label: 'デフォルト倉庫' },
            { name: 'default_location', label: 'デフォルト棚番' },
            { name: 'provision_type', label: '支給種別', type: 'select', options: [
                { value: 'paid', label: '有償支給' }, { value: 'free', label: '無償支給' }, { value: 'none', label: '支給なし' }
            ]},
            { name: 'description', label: '説明' }
        ],
        supplier: [ { name: 'supplier_number', label: 'サプライヤー番号' }, { name: 'name', label: 'サプライヤー名' }, { name: 'contact_person', label: '担当者名' }, { name: 'phone', label: '電話番号' }, { name: 'email', label: 'メールアドレス', type: 'email' }, { name: 'address', label: '住所' } ],
        warehouse: [ { name: 'warehouse_number', label: '倉庫番号' }, { name: 'name', label: '倉庫名' }, { name: 'location', label: '所在地' } ],
        'inventory-purchase-entry': [
            { name: 'order_number', label: '発注番号' },
            { name: 'shipment_number', label: '便番号' },
            { name: 'supplier', label: '仕入れ先' },
            { name: 'item', label: '発注対象' },
            { name: 'part_number', label: '品番' },
            { name: 'product_name', label: '品名' },
            { name: 'quantity', label: '数量', type: 'number' },
            { name: 'expected_arrival', label: '入荷予定日', type: 'date' }
            // 'status' is read-only and should not be in the form
        ],
        'production-plan-entry': [
            { name: 'plan_name', label: '計画名' },
            { name: 'product_code', label: '製品コード' },
            { name: 'production_plan', label: '参照生産計画' },
            { name: 'planned_quantity', label: '計画数量', type: 'number' },
            { name: 'planned_start_datetime', label: '計画開始日時', type: 'datetime-local' },
            { name: 'planned_end_datetime', label: '計画終了日時', type: 'datetime-local' },
            { name: 'remarks', label: '備考' }
        ],
        'parts-used-entry': [ { name: 'production_plan', label: '生産計画' }, { name: 'part_code', label: '部品コード' }, { name: 'warehouse', label: '倉庫' }, { name: 'quantity_used', label: '使用数量', type: 'number' }, { name: 'used_datetime', label: '使用日時', type: 'datetime-local' } ],
    };
    return allFields[type] || [];
};

const getTableConfig = (type) => {
    let headers = [], rowKeys = [], idKey = 'id';
    switch (type) {
        case 'item':
            headers = ['コード', '品番名', '品目タイプ', '単位', 'デフォルト倉庫', 'デフォルト棚番', '支給種別', '説明', '操作'];
            rowKeys = ['code', 'name', 'item_type', 'unit', 'default_warehouse', 'default_location', 'provision_type', 'description'];
            break;
        case 'supplier':
            headers = ['サプライヤー番号', 'サプライヤー名', '担当者名', '電話番号', 'メールアドレス', '住所', '操作'];
            rowKeys = ['supplier_number', 'name', 'contact_person', 'phone', 'email', 'address'];
            break;
        case 'warehouse':
            headers = ['倉庫番号', '倉庫名', '所在地', '操作'];
            rowKeys = ['warehouse_number', 'name', 'location'];
            break;
        case 'inventory-purchase-entry':
            headers = ['発注番号', '便番号', '仕入れ先', '発注対象', '品番', '品名', '数量', '入荷予定日', 'ステータス', '操作'];
            rowKeys = ['order_number', 'shipment_number', 'supplier', 'item', 'part_number', 'product_name', 'quantity', 'expected_arrival', 'status'];
            break;
        case 'production-plan-entry':
            headers = ['計画名', '製品コード', '計画数量', '計画開始日時', '計画終了日時', 'ステータス', '操作'];
            rowKeys = ['plan_name', 'product_code', 'planned_quantity', 'planned_start_datetime', 'planned_end_datetime', 'status'];
            break;
        case 'parts-used-entry':
            headers = ['生産計画', '部品コード', '倉庫', '使用数量', '使用日時', '操作'];
            rowKeys = ['production_plan', 'part_code', 'warehouse', 'quantity_used', 'used_datetime'];
            break;
        default: break;
    }
    return { headers, rowKeys, idKey };
};

const DATA_CONFIG = {
    'item': { name: '品番マスター', listUrl: '/api/master/item/list/ajax/', createUrl: '/api/master/item/create/ajax/', detailUrl: (id) => `/api/master/item/${id}/detail/ajax/`, deleteUrl: (id) => `/api/master/item/${id}/delete/ajax/` },
    'supplier': { name: 'サプライヤーマスター', listUrl: '/api/master/supplier/list/ajax/', createUrl: '/api/master/supplier/create/ajax/', detailUrl: (id) => `/api/master/supplier/${id}/detail/ajax/`, deleteUrl: (id) => `/api/master/supplier/${id}/delete/ajax/` },
    'warehouse': { name: '倉庫マスター', listUrl: '/api/master/warehouse/list/ajax/', createUrl: '/api/master/warehouse/create/ajax/', detailUrl: (id) => `/api/master/warehouse/${id}/detail/ajax/`, deleteUrl: (id) => `/api/master/warehouse/${id}/delete/ajax/` },
    // Assuming other apps follow a similar URL pattern (kebab-case)
    'inventory-purchase-entry': { name: '入庫予定', listUrl: '/api/inventory/purchase-order/list/ajax/', createUrl: '/api/inventory/purchase-order/create/ajax/', detailUrl: (id) => `/api/inventory/purchase-order/${id}/detail/ajax/`, deleteUrl: (id) => `/api/inventory/purchase-order/${id}/delete/ajax/` },
    'production-plan-entry': { name: '生産計画', listUrl: '/api/production/production-plan/list/ajax/', createUrl: '/api/production/production-plan/create/ajax/', detailUrl: (id) => `/api/production/production-plan/${id}/detail/ajax/`, deleteUrl: (id) => `/api/production/production-plan/${id}/delete/ajax/` },
    'parts-used-entry': { name: '使用部品', listUrl: '/api/production/parts-used/list/ajax/', createUrl: '/api/production/parts-used/create/ajax/', detailUrl: (id) => `/api/production/parts-used/${id}/detail/ajax/`, deleteUrl: (id) => `/api/production/parts-used/${id}/delete/ajax/` },
};

const MASTER_CARDS = ['item', 'supplier', 'warehouse'];
const BUSINESS_CARDS = ['inventory-purchase-entry', 'production-plan-entry', 'parts-used-entry'];

const CSV_DATA_TYPES = [
    {
        label: "マスターデータ",
        options: [
            { value: "item", label: "品番マスター", templateUrl: "/api/master/item/csv-template/", uploadUrl: "/api/master/item/import-csv/" },
            { value: "supplier", label: "サプライヤーマスター", templateUrl: "/api/master/supplier/csv-template/", uploadUrl: "/api/master/supplier/import-csv/" },
            { value: "warehouse", label: "倉庫マスター", templateUrl: "/api/master/warehouse/csv-template/", uploadUrl: "/api/master/warehouse/import-csv/" },
        ]
    },
    {
        label: "業務データ",
        options: [
            { value: "purchase_order", label: "入庫予定", templateUrl: "/api/inventory/purchase-order/csv-template/", uploadUrl: "/api/inventory/purchase-order/import-csv/" },
            { value: "production_plan", label: "生産計画", templateUrl: "/api/production/plan/csv-template/", uploadUrl: "/api/production/plan/import-csv/" },
            { value: "parts_used", label: "使用部品", templateUrl: "/api/production/parts-used/csv-template/", uploadUrl: "/api/production/parts-used/import-csv/" },
        ]
    }
];

const DataImport = () => {
    // State for modals
    const [showRegisterModal, setShowRegisterModal] = useState(false);
    const [showListModal, setShowListModal] = useState(false);
    const [showDeleteModal, setShowDeleteModal] = useState(false);
    const [showCsvResultModal, setShowCsvResultModal] = useState(false);

    // State for modal content
    const [modalConfig, setModalConfig] = useState({ type: '', name: '', recordId: null });
    const [listData, setListData] = useState({ headers: [], rows: [], rowKeys: [], idKey: 'id' });
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState(null);
    const [formData, setFormData] = useState({});
    const [itemToDelete, setItemToDelete] = useState(null);
    const [csvResult, setCsvResult] = useState({ message: '', isError: false, errors: [] });

    // State for CSV Upload
    const [csvDataType, setCsvDataType] = useState('');
    const [csvFile, setCsvFile] = useState(null);
    const [csvUploadUrl, setCsvUploadUrl] = useState('');
    const [csvTemplateUrl, setCsvTemplateUrl] = useState('');

    const handleShowRegisterModal = useCallback(async (type, recordId = null) => {
        const config = DATA_CONFIG[type];
        const fields = getFormFields(type); // フィールド定義を取得
        setModalConfig({ type, name: config.name, recordId });
        setFormData({});
        if (recordId) {
            setIsLoading(true);
            setError(null); // エラーをリセット
            try {
                const response = await fetch(config.detailUrl(recordId), { credentials: 'include' });
                if (!response.ok) throw new Error('Failed to fetch record details.');
                const result = await response.json();
                if (result.status === 'success') {
                    const fetchedData = result.data;
                    const processedData = { ...fetchedData };

                    // プルダウンのフィールドについて、表示名からDBの値に変換する
                    fields.forEach(field => {
                        if (field.type === 'select' && fetchedData[field.name]) {
                            const apiValue = fetchedData[field.name];
                            const optionByLabel = field.options.find(opt => opt.label === apiValue);
                            const optionByValue = field.options.find(opt => opt.value === apiValue);

                            if (optionByLabel && !optionByValue) {
                                // APIからの値が表示名と一致し、DB値とは異なる場合、DB値に変換
                                processedData[field.name] = optionByLabel.value;
                            } else if (!optionByLabel && !optionByValue) {
                                // どの選択肢とも一致しない場合は値をクリアして警告を回避
                                processedData[field.name] = '';
                            }
                        }
                    });
                    setFormData(processedData);
                } else {
                    throw new Error(result.message || 'Could not load data.');
                }
            } catch (e) {
                setError(e.message);
            } finally {
                setIsLoading(false);
            }
        }
        setShowRegisterModal(true);
    }, []);

    const handleShowListModal = useCallback((type) => {
        setModalConfig({ type, name: DATA_CONFIG[type].name });
        setShowListModal(true);
    }, []);

    useEffect(() => {
        if (!showListModal || !modalConfig.type) return;
        const fetchListData = async () => {
            setIsLoading(true);
            setError(null);
            try {
                const response = await fetch(DATA_CONFIG[modalConfig.type].listUrl, { credentials: 'include' });
                if (!response.ok) throw new Error('Network response was not ok');
                const result = await response.json();
                setListData({ ...getTableConfig(modalConfig.type), rows: result.data });
            } catch (e) { setError(e.message); } finally { setIsLoading(false); }
        };
        fetchListData();
    }, [showListModal, modalConfig]);

    const handleFormSubmit = async () => {
        const { type, recordId } = modalConfig;
        const config = DATA_CONFIG[type];
        const submitData = new FormData();
        Object.keys(formData).forEach(key => submitData.append(key, formData[key]));
        if (recordId) submitData.append('id', recordId);

        try {
            const response = await fetch(config.createUrl, { method: 'POST', body: submitData, headers: { 'X-CSRFToken': getCsrfToken() }, credentials: 'include' });
            const result = await response.json();
            if (result.status === 'success') {
                alert(result.message || '保存しました。');
                setShowRegisterModal(false);
                if (showListModal) setModalConfig(prev => ({...prev})); // Refresh list
            } else {
                const errorMessages = Object.entries(result.errors || {}).map(([field, errors]) => `${field}: ${errors.join(', ')}`).join('\n');
                alert(`エラー:\n${result.message || ''}\n${errorMessages}`);
            }
        } catch (e) { alert('保存中に通信エラーが発生しました。'); }
    };

    const handleDeleteConfirm = async () => {
        if (!itemToDelete) return;
        const { type, id } = itemToDelete;
        try {
            const response = await fetch(DATA_CONFIG[type].deleteUrl(id), { method: 'POST', headers: { 'X-CSRFToken': getCsrfToken(), 'Content-Type': 'application/json' }, credentials: 'include' });
            const result = await response.json();
            if (result.status === 'success') {
                alert(result.message || '削除しました。');
                setShowDeleteModal(false);
                setListData(prev => ({ ...prev, rows: prev.rows.filter(row => row.id !== id) }));
            } else {
                alert(`エラー: ${result.message || '削除に失敗しました。'}`);
            }
        } catch (e) { alert('削除処理中にエラーが発生しました。'); }
    };

    const onDrop = useCallback(acceptedFiles => setCsvFile(acceptedFiles[0]), []);
    const { getRootProps, getInputProps, isDragActive } = useDropzone({ onDrop, accept: { 'text/csv': ['.csv'] }, multiple: false });

    const handleCsvDataTypeChange = (e) => {
        const value = e.target.value;
        setCsvDataType(value);
        const selectedOption = CSV_DATA_TYPES.flatMap(g => g.options).find(o => o.value === value);
        setCsvUploadUrl(selectedOption?.uploadUrl || '');
        setCsvTemplateUrl(selectedOption?.templateUrl || '');
    };

    const handleTemplateDownload = async (e) => {
        e.preventDefault();
        if (!csvTemplateUrl) return;

        try {
            // fetchを使用してプロキシ経由でリクエストを送信します
            const response = await fetch(csvTemplateUrl, { credentials: 'include' });
            if (!response.ok) {
                throw new Error(`サーバーエラー: ${response.status} ${response.statusText}`);
            }

            // ヘッダーからファイル名を取得します
            const disposition = response.headers.get('Content-Disposition');
            let filename = 'template.csv'; // デフォルトのファイル名
            if (disposition && disposition.includes('attachment')) {
                const filenameMatch = /filename="([^"]+)"/.exec(disposition);
                if (filenameMatch && filenameMatch[1]) {
                    filename = decodeURIComponent(filenameMatch[1]);
                }
            }

            const blob = await response.blob();
            const downloadUrl = window.URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = downloadUrl;
            link.download = filename;
            link.click();
            window.URL.revokeObjectURL(downloadUrl);
        } catch (err) {
            console.error('テンプレートのダウンロードに失敗しました:', err);
            alert(`テンプレートのダウンロードに失敗しました: ${err.message}`);
        }
    };

    const handleCsvUpload = async (e) => {
        e.preventDefault();
        if (!csvFile || !csvUploadUrl) return;
        const uploadData = new FormData();
        uploadData.append('csv_file', csvFile);
        uploadData.append('data_type', csvDataType);
        setIsLoading(true);
        try {
            const response = await fetch(csvUploadUrl, { method: 'POST', body: uploadData, headers: { 'X-CSRFToken': getCsrfToken() }, credentials: 'include' });
            const result = await response.json();
            setCsvResult({ message: result.message, isError: result.status !== 'success' && result.status !== 'partial_success', errors: result.errors || [] });
        } catch (err) {
            setCsvResult({ message: `アップロード中にエラーが発生しました: ${err.message}`, isError: true, errors: [] });
        } finally {
            setIsLoading(false);
            setShowCsvResultModal(true);
            setCsvFile(null);
        }
    };

    const renderCard = (type, isBusiness = false) => {
        const config = DATA_CONFIG[type];
        return (
            <Col md={4} className="mb-3" key={type}>
                <Card className="h-100">
                    <Card.Body className="d-flex flex-column">
                        <Card.Title>{config.name}</Card.Title>
                        <Card.Text className="small">新しい{config.name}データを登録します。</Card.Text>
                        <Button variant={isBusiness ? "info" : "primary"} className="w-100 mt-auto mb-2" onClick={() => handleShowRegisterModal(type)}>
                            {config.name}登録
                        </Button>
                        <Button variant="outline-secondary" className="w-100" onClick={() => handleShowListModal(type)}>
                            {config.name}呼び出し
                        </Button>
                    </Card.Body>
                </Card>
            </Col>
        );
    };

  return (
    <Container className="mt-4">
      <h2>データ投入</h2>

      <h3 className="mt-4">マスターデータ登録</h3>
      <p>登録または呼び出したいマスターを選択してください。</p>
      <Row>{MASTER_CARDS.map(type => renderCard(type, false))}</Row>

      <h3 className="mt-5">業務データ登録</h3>
      <p>登録したい業務データを選択してください。</p>
      <Row>{BUSINESS_CARDS.map(type => renderCard(type, true))}</Row>

      <h3 className="mt-5">CSVデータ一括登録</h3>
      <p>登録したいデータの種類を選択し、CSVファイルをアップロードしてください。</p>
      <Card className="mb-5">
        <Card.Body>
          <Form onSubmit={handleCsvUpload}>
            <Row className="g-3 align-items-end">
              <Col md={5}>
                <Form.Label htmlFor="csvDataType">データ種類</Form.Label>
                <Form.Select id="csvDataType" value={csvDataType} onChange={handleCsvDataTypeChange} required>
                  <option value="" disabled>選択してください...</option>
                  {CSV_DATA_TYPES.map(group => (
                    <optgroup label={group.label} key={group.label}>
                      {group.options.map(opt => <option key={opt.value} value={opt.value}>{opt.label}</option>)}
                    </optgroup>
                  ))}
                </Form.Select>
              </Col>
              <Col md={5}>
                <Form.Label>CSVファイル <span className="text-muted small">(ドラッグ＆ドロップまたはクリックで選択)</span></Form.Label>
                <div {...getRootProps()} style={{ border: '2px dashed #ccc', padding: '20px', textAlign: 'center', cursor: 'pointer', borderRadius: '.25rem', borderColor: isDragActive ? '#007bff' : '#ccc' }}>
                  <input {...getInputProps()} />
                  {csvFile ? <p className="my-2 small">{csvFile.name}</p> : <p className="my-2 small text-muted">ここにファイルをドラッグ＆ドロップするか、クリックして選択</p>}
                </div>
              </Col>
              <Col md={2}>
                <Button type="submit" variant="success" className="w-100" disabled={!csvDataType || !csvFile || isLoading}>
                  {isLoading ? <Spinner as="span" animation="border" size="sm" /> : 'アップロード'}
                </Button>
              </Col>
            </Row>
            <div className="mt-3">
              {csvTemplateUrl && <a href={csvTemplateUrl} onClick={handleTemplateDownload} className="btn btn-link btn-sm p-0">テンプレートCSVをダウンロード</a>}
            </div>
          </Form>
        </Card.Body>
      </Card>

      <Modal show={showRegisterModal} onHide={() => setShowRegisterModal(false)} size="lg" centered backdrop="static">
        <Modal.Header closeButton><Modal.Title>{modalConfig.name} {modalConfig.recordId ? '修正' : '登録'}</Modal.Title></Modal.Header>
        <Modal.Body>
          {isLoading ? <Spinner animation="border" /> : error ? <Alert variant="danger">{error}</Alert> : <GenericForm fields={getFormFields(modalConfig.type)} formData={formData} setFormData={setFormData} />}
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setShowRegisterModal(false)}>閉じる</Button>
          <Button variant="success" onClick={handleFormSubmit}>保存</Button>
        </Modal.Footer>
      </Modal>

      <Modal show={showListModal} onHide={() => setShowListModal(false)} size="xl" centered scrollable>
        <Modal.Header closeButton><Modal.Title>{modalConfig.name} 一覧</Modal.Title></Modal.Header>
        <Modal.Body>
          {isLoading && <div className="text-center"><Spinner animation="border" /><p>データを読み込んでいます...</p></div>}
          {error && <Alert variant="danger">データの読み込みに失敗しました: {error}</Alert>}
          {!isLoading && !error && (listData.rows.length > 0 ? (
            <Table striped bordered hover responsive size="sm">
              <thead><tr>{listData.headers.map(h => <th key={h}>{h}</th>)}</tr></thead>
              <tbody>
                {listData.rows.map(row => (
                  <tr key={row[listData.idKey]}>
                    {listData.rowKeys.map(key => <td key={key}>{String(row[key] ?? '')}</td>)}
                    <td>
                      <Button variant="warning" size="sm" className="me-1" onClick={() => { setShowListModal(false); handleShowRegisterModal(modalConfig.type, row[listData.idKey]); }}>修正</Button>
                      <Button variant="danger" size="sm" onClick={() => {
                        const {type} = modalConfig;
                        const displayName = row.name || row.order_number || row.plan_name || `ID: ${row[listData.idKey]}`;
                        setItemToDelete({ id: row[listData.idKey], type, displayName });
                        setShowDeleteModal(true);
                      }}>削除</Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </Table>
          ) : <p className="text-center">登録されているデータはありません。</p>)}
        </Modal.Body>
        <Modal.Footer><Button variant="secondary" onClick={() => setShowListModal(false)}>閉じる</Button></Modal.Footer>
      </Modal>

      <Modal show={showDeleteModal} onHide={() => setShowDeleteModal(false)} centered>
        <Modal.Header closeButton><Modal.Title>削除確認</Modal.Title></Modal.Header>
        <Modal.Body>本当に「<strong>{itemToDelete?.displayName}</strong>」を削除しますか？この操作は元に戻せません。</Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setShowDeleteModal(false)}>キャンセル</Button>
          <Button variant="danger" onClick={handleDeleteConfirm}>削除実行</Button>
        </Modal.Footer>
      </Modal>

      <Modal show={showCsvResultModal} onHide={() => setShowCsvResultModal(false)} centered>
        <Modal.Header closeButton><Modal.Title>CSVアップロード結果</Modal.Title></Modal.Header>
        <Modal.Body>
          <Alert variant={csvResult.isError ? 'danger' : 'success'}>{csvResult.message}</Alert>
          {csvResult.errors && csvResult.errors.length > 0 && (
            <div className="mt-3" style={{ maxHeight: '200px', overflowY: 'auto', background: '#f8f9fa', padding: '10px', borderRadius: '5px' }}>
              <strong>エラー詳細:</strong>
              <ul className="mb-0 ps-3">
                {csvResult.errors.map((error, index) => <li key={index}><small>{error}</small></li>)}
              </ul>
            </div>
          )}
        </Modal.Body>
        <Modal.Footer><Button variant="primary" onClick={() => setShowCsvResultModal(false)}>閉じる</Button></Modal.Footer>
      </Modal>
    </Container>
  );
};

export default DataImport;