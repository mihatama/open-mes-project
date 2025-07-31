import React, { useState, useEffect, useCallback } from 'react';
import { Container, Table, Button, Modal, Form, Spinner, Alert, Row, Col } from 'react-bootstrap';
import { getCookie } from '../utils/cookies';

const DATA_TYPE_CHOICES = [
    { value: 'item', label: '品番マスター' },
    { value: 'supplier', label: 'サプライヤーマスター' },
    { value: 'warehouse', label: '倉庫マスター' },
    { value: 'purchase_order', label: '入庫予定' },
    { value: 'production_plan', label: '生産計画' },
    { value: 'parts_used', label: '使用部品' },
];

const CsvMappingSettings = () => {
    const [mappings, setMappings] = useState([]);
    const [selectedDataType, setSelectedDataType] = useState(DATA_TYPE_CHOICES[0].value);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    const [showModal, setShowModal] = useState(false);
    const [isEditing, setIsEditing] = useState(false);
    const [currentMapping, setCurrentMapping] = useState(null);
    const [formErrors, setFormErrors] = useState({});

    const fetchMappings = useCallback(async (dataType) => {
        setLoading(true);
        setError(null);
        try {
            const response = await fetch(`/api/base/csv-mappings/?data_type=${dataType}`);
            if (!response.ok) throw new Error('データの取得に失敗しました。');
            const data = await response.json();
            // orderでソート
            const sortedData = data.sort((a, b) => a.order - b.order);
            setMappings(sortedData);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        if (selectedDataType) {
            fetchMappings(selectedDataType);
        }
    }, [selectedDataType, fetchMappings]);

    const handleOpenModal = (mapping = null) => {
        setIsEditing(!!mapping);
        setCurrentMapping(mapping ? { ...mapping } : {
            data_type: selectedDataType,
            csv_header: '',
            model_field_name: '',
            display_name: '',
            order: mappings.length > 0 ? Math.max(...mappings.map(m => m.order)) + 10 : 10,
            is_required: true,
            is_active: true,
        });
        setFormErrors({});
        setShowModal(true);
    };

    const handleCloseModal = () => {
        setShowModal(false);
        setCurrentMapping(null);
    };

    const handleFormChange = (e) => {
        const { name, value, type, checked } = e.target;
        setCurrentMapping(prev => ({
            ...prev,
            [name]: type === 'checkbox' ? checked : value
        }));
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setFormErrors({});
        const url = isEditing ? `/api/base/csv-mappings/${currentMapping.id}/` : '/api/base/csv-mappings/';
        const method = isEditing ? 'PUT' : 'POST';

        try {
            const response = await fetch(url, {
                method,
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken'),
                },
                body: JSON.stringify(currentMapping),
            });
            const result = await response.json();
            if (!response.ok) {
                setFormErrors(result);
                throw new Error('保存に失敗しました。入力内容を確認してください。');
            }
            handleCloseModal();
            fetchMappings(selectedDataType);
        } catch (err) {
            alert(err.message);
        }
    };

    const handleDelete = async (id) => {
        if (window.confirm('このマッピングを削除しますか？')) {
            try {
                const response = await fetch(`/api/base/csv-mappings/${id}/`, {
                    method: 'DELETE',
                    headers: { 'X-CSRFToken': getCookie('csrftoken') },
                });
                if (response.status !== 204) throw new Error('削除に失敗しました。');
                fetchMappings(selectedDataType);
            } catch (err) {
                alert(err.message);
            }
        }
    };

    return (
        <Container fluid className="mt-4">
            <h2>CSVマッピング設定</h2>
            <p>CSVインポート時の列名とシステムの項目を紐付けます。</p>

            <Row className="mb-3 align-items-end">
                <Col md={4}>
                    <Form.Group>
                        <Form.Label>データ種別</Form.Label>
                        <Form.Select value={selectedDataType} onChange={e => setSelectedDataType(e.target.value)}>
                            {DATA_TYPE_CHOICES.map(choice => (
                                <option key={choice.value} value={choice.value}>{choice.label}</option>
                            ))}
                        </Form.Select>
                    </Form.Group>
                </Col>
                <Col>
                    <Button variant="primary" onClick={() => handleOpenModal()}>
                        新規マッピング追加
                    </Button>
                </Col>
            </Row>

            {loading && <Spinner animation="border" />}
            {error && <Alert variant="danger">{error}</Alert>}
            {!loading && !error && (
                <Table striped bordered hover responsive>
                    <thead>
                        <tr>
                            <th>表示順</th><th>CSVヘッダー名</th><th>モデルフィールド名</th><th>表示名</th><th>必須</th><th>有効</th><th>操作</th>
                        </tr>
                    </thead>
                    <tbody>
                        {mappings.map(mapping => (
                            <tr key={mapping.id}>
                                <td>{mapping.order}</td><td>{mapping.csv_header}</td><td>{mapping.model_field_name}</td><td>{mapping.display_name}</td>
                                <td className="text-center">{mapping.is_required ? '✔' : ''}</td><td className="text-center">{mapping.is_active ? '✔' : ''}</td>
                                <td>
                                    <Button variant="info" size="sm" onClick={() => handleOpenModal(mapping)}>編集</Button>{' '}
                                    <Button variant="danger" size="sm" onClick={() => handleDelete(mapping.id)}>削除</Button>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </Table>
            )}

            <Modal show={showModal} onHide={handleCloseModal} centered>
                <Modal.Header closeButton><Modal.Title>{isEditing ? 'マッピング編集' : '新規マッピング追加'}</Modal.Title></Modal.Header>
                <Form onSubmit={handleSubmit}>
                    <Modal.Body>
                        {currentMapping && (
                            <>
                                <Form.Group className="mb-3"><Form.Label>データ種別</Form.Label><Form.Control type="text" value={DATA_TYPE_CHOICES.find(c => c.value === currentMapping.data_type)?.label || ''} readOnly disabled /></Form.Group>
                                <Form.Group className="mb-3"><Form.Label>CSVヘッダー名</Form.Label><Form.Control type="text" name="csv_header" value={currentMapping.csv_header} onChange={handleFormChange} isInvalid={!!formErrors.csv_header} required /><Form.Control.Feedback type="invalid">{formErrors.csv_header}</Form.Control.Feedback></Form.Group>
                                <Form.Group className="mb-3"><Form.Label>モデルフィールド名</Form.Label><Form.Control type="text" name="model_field_name" value={currentMapping.model_field_name} onChange={handleFormChange} isInvalid={!!formErrors.model_field_name} required /><Form.Control.Feedback type="invalid">{formErrors.model_field_name}</Form.Control.Feedback></Form.Group>
                                <Form.Group className="mb-3"><Form.Label>表示名</Form.Label><Form.Control type="text" name="display_name" value={currentMapping.display_name} onChange={handleFormChange} isInvalid={!!formErrors.display_name} required /><Form.Control.Feedback type="invalid">{formErrors.display_name}</Form.Control.Feedback></Form.Group>
                                <Form.Group className="mb-3"><Form.Label>表示順</Form.Label><Form.Control type="number" name="order" value={currentMapping.order} onChange={handleFormChange} isInvalid={!!formErrors.order} required /><Form.Control.Feedback type="invalid">{formErrors.order}</Form.Control.Feedback></Form.Group>
                                <Form.Check type="switch" id="is_required" name="is_required" label="必須項目" checked={currentMapping.is_required} onChange={handleFormChange} className="mb-2" />
                                <Form.Check type="switch" id="is_active" name="is_active" label="有効" checked={currentMapping.is_active} onChange={handleFormChange} />
                                {formErrors.non_field_errors && <Alert variant="danger" className="mt-3">{formErrors.non_field_errors.join(' ')}</Alert>}
                                {formErrors.detail && <Alert variant="danger" className="mt-3">{formErrors.detail}</Alert>}
                            </>
                        )}
                    </Modal.Body>
                    <Modal.Footer>
                        <Button variant="secondary" onClick={handleCloseModal}>キャンセル</Button>
                        <Button variant="primary" type="submit">保存</Button>
                    </Modal.Footer>
                </Form>
            </Modal>
        </Container>
    );
};

export default CsvMappingSettings;