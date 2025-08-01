import React, { useState, useEffect, useCallback } from 'react';
import { Container, Table, Button, Form, Spinner, Alert, Row, Col, Tooltip, OverlayTrigger } from 'react-bootstrap';
import { DragDropContext, Droppable, Draggable } from '@hello-pangea/dnd';
import { getCookie } from '../utils/cookies';

// This could be moved to a shared constants file
const DATA_TYPE_CHOICES = [
    { value: 'item', label: '品番マスター' },
    { value: 'supplier', label: 'サプライヤーマスター' },
    { value: 'warehouse', label: '倉庫マスター' },
    { value: 'purchase_order', label: '入庫予定' },
    { value: 'production_plan', label: '生産計画' },
    { value: 'parts_used', label: '使用部品' },
];

const ModelDisplaySettings = () => {
    const [fieldsData, setFieldsData] = useState([]);
    const [selectedDataType, setSelectedDataType] = useState(DATA_TYPE_CHOICES[0].value);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [isSaving, setIsSaving] = useState(false);
    const [saveStatus, setSaveStatus] = useState({ message: '', variant: '', show: false });

    const fetchAllData = useCallback(async (dataType) => {
        setLoading(true);
        setError(null);
        setSaveStatus(prev => ({ ...prev, show: false }));
        try {
            const [settingsRes, fieldsRes] = await Promise.all([
                fetch(`/api/base/model-display-settings/?data_type=${dataType}`),
                fetch(`/api/base/model-fields/?data_type=${dataType}`)
            ]);

            if (!settingsRes.ok) throw new Error(`表示設定の取得に失敗しました: ${settingsRes.statusText}`);
            if (!fieldsRes.ok) throw new Error(`モデル情報の取得に失敗しました: ${fieldsRes.statusText}`);

            const settings = await settingsRes.json();
            const modelFields = await fieldsRes.json();

            const data = modelFields
                .filter(field => field.name !== 'id') // 'id'フィールドは設定対象外
                .map((field, index) => {
                const existingSetting = settings.find(s => s.model_field_name === field.name);

                return {
                    // Model field info (read-only)
                    model_field_name: field.name,
                    verbose_name: field.verbose_name,
                    display_name: existingSetting?.display_name || '',
                    help_text: field.help_text,
                    display_order: existingSetting?.display_order ?? (index + 1) * 10, // Use ?? to allow order 0
                };
            });

            data.sort((a, b) => a.display_order - b.display_order);
            setFieldsData(data);

        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        if (selectedDataType) {
            fetchAllData(selectedDataType);
        }
    }, [selectedDataType, fetchAllData]);

    const handleInputChange = (index, e) => {
        const { name, value, type, checked } = e.target;
        const newFieldsData = [...fieldsData];
        newFieldsData[index] = {
            ...newFieldsData[index],
            [name]: type === 'checkbox' ? checked : value // 'switch' type is no longer used in this component
        };
        setFieldsData(newFieldsData);
    };

    const handleSave = async () => {
        setIsSaving(true);
        setSaveStatus({ message: '', variant: '', show: false });

        const payload = fieldsData.map(item => ({
            model_field_name: item.model_field_name,
            display_name: item.display_name,
            display_order: Number(item.display_order) || 0,
        }));

        try {
            const response = await fetch(`/api/base/model-display-settings/bulk-save/?data_type=${selectedDataType}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken'),
                },
                body: JSON.stringify(payload),
            });
            const result = await response.json();
            if (!response.ok) {
                console.error('Save failed:', result);
                throw new Error(result.message || '保存に失敗しました。');
            }
            setSaveStatus({ message: result.message, variant: 'success', show: true });
            fetchAllData(selectedDataType);
        } catch (err) {
            setSaveStatus({ message: err.message, variant: 'danger', show: true });
        } finally {
            setIsSaving(false);
        }
    };

    const handleDragEnd = (result) => {
        if (!result.destination) {
            return;
        }

        const items = Array.from(fieldsData);
        const [reorderedItem] = items.splice(result.source.index, 1);
        items.splice(result.destination.index, 0, reorderedItem);

        const updatedItems = items.map((item, index) => ({
            ...item,
            display_order: (index + 1) * 10,
        }));

        setFieldsData(updatedItems);
    };

    return (
        <Container fluid className="mt-4">
            <h2>モデル項目表示設定</h2>
            <p>各データ種別の一覧画面に表示する項目やその順序、幅をカスタマイズします。</p>

            <Row className="my-3 p-3 bg-light border rounded align-items-center">
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
                    <Button variant="primary" onClick={handleSave} disabled={loading || isSaving}>
                        {isSaving ? <><Spinner as="span" animation="border" size="sm" role="status" aria-hidden="true" /> 保存中...</> : 'この設定で保存'}
                    </Button>
                </Col>
            </Row>

            {saveStatus.show && <Alert variant={saveStatus.variant} onClose={() => setSaveStatus(prev => ({ ...prev, show: false }))} dismissible>{saveStatus.message}</Alert>}
            {loading && <Spinner animation="border" />}
            {error && <Alert variant="danger">{error}</Alert>}

            {!loading && !error && (
                <DragDropContext onDragEnd={handleDragEnd}>
                    <Table striped bordered hover responsive>
                        <thead>
                            <tr>
                                <th style={{ width: '60px' }}>順序</th>
                                <th style={{ minWidth: '180px' }}>モデル項目</th>
                                <th style={{ minWidth: '180px' }}>カスタム表示名</th>
                            </tr>
                        </thead>
                        <Droppable droppableId="model-display-droppable">
                            {(provided) => (
                                <tbody {...provided.droppableProps} ref={provided.innerRef}>
                                    {fieldsData.map((item, index) => (
                                        <Draggable key={item.model_field_name} draggableId={item.model_field_name} index={index}>
                                            {(provided, snapshot) => (
                                                <tr
                                                    ref={provided.innerRef}
                                                    {...provided.draggableProps}
                                                    className={`${snapshot.isDragging ? 'table-info' : ''}`}
                                                    style={{ ...provided.draggableProps.style }}
                                                >
                                                    <td className="text-center align-middle" {...provided.dragHandleProps} style={{ cursor: 'grab' }}>
                                                        <span title="ドラッグして順序を変更">↕</span>
                                                    </td>
                                                    <td className="align-middle">
                                                        <OverlayTrigger placement="top" overlay={<Tooltip id={`tooltip-${index}`}>{`フィールド名: ${item.model_field_name}`}<br />{`ヘルプ: ${item.help_text || 'なし'}`}</Tooltip>}>
                                                            <span>{item.verbose_name}</span>
                                                        </OverlayTrigger>
                                                    </td>
                                                    <td className="align-middle">
                                                        <Form.Control type="text" name="display_name" value={item.display_name || ''} onChange={(e) => handleInputChange(index, e)} placeholder={item.verbose_name} />
                                                    </td>
                                                </tr>
                                            )}
                                        </Draggable>
                                    ))}
                                    {provided.placeholder}
                                </tbody>
                            )}
                        </Droppable>
                    </Table>
                </DragDropContext>
            )}
        </Container>
    );
};

export default ModelDisplaySettings;