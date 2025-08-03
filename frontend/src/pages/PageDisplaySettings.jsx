import React, { useState, useEffect, useCallback } from 'react';
import { Container, Table, Button, Form, Spinner, Alert, Row, Col, Tooltip, OverlayTrigger } from 'react-bootstrap';
import { DragDropContext, Droppable, Draggable } from '@hello-pangea/dnd';
import { getCookie } from '../utils/cookies';

// This could be moved to a shared constants file
const DATA_TYPE_CHOICES = [
    { value: 'goods_receipt', label: '入庫処理' }, // This now represents combined fields from PurchaseOrder and GoodsReceipt
];

const PageDisplaySettings = () => {
    const [fieldsData, setFieldsData] = useState([]);
    const [selectedDataType, setSelectedDataType] = useState(DATA_TYPE_CHOICES[0].value);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [isSaving, setIsSaving] = useState(false);
    const [saveStatus, setSaveStatus] = useState({ message: '', variant: '', show: false });

    const fetchAllData = useCallback(async (selectedType) => {
        setLoading(true);
        setError(null);
        setSaveStatus(prev => ({ ...prev, show: false }));
        try {
            let settings = [];
            let modelFields = [];

            // 「入庫処理」が選択された場合、入庫予定と入庫実績の両方のデータを取得して結合する
            if (selectedType === 'goods_receipt') {
                const dataTypesToFetch = ['purchase_order', 'goods_receipt'];
                
                const promises = dataTypesToFetch.flatMap(type => [
                    fetch(`/api/base/model-display-settings/?data_type=${type}`),
                    fetch(`/api/base/model-fields/?data_type=${type}`)
                ]);

                const responses = await Promise.all(promises);

                for (const res of responses) {
                    if (!res.ok) {
                        const errorText = await res.text();
                        throw new Error(`データの取得に失敗しました (${res.status} ${res.statusText}): ${errorText}`);
                    }
                }
                
                const results = await Promise.all(responses.map(res => res.json()));
                
                const poSettings = results[0];
                const poFields = results[1];
                const grSettings = results[2];
                const grFields = results[3];

                // 設定を結合
                settings = [...poSettings, ...grSettings];
                
                // フィールドを結合（重複を排除し、どのモデル由来かを示す情報を付与）
                const combinedFieldsMap = new Map();
                poFields.forEach(field => {
                    if (field.name !== 'id') {
                        combinedFieldsMap.set(field.name, { ...field, model_source: '入庫予定' });
                    }
                });
                grFields.forEach(field => {
                    if (field.name !== 'id' && !combinedFieldsMap.has(field.name)) {
                        combinedFieldsMap.set(field.name, { ...field, model_source: '入庫実績' });
                    }
                });
                modelFields = Array.from(combinedFieldsMap.values());
            }

            const data = modelFields
                .map((field, index) => {
                const existingSetting = settings.find(s => s.model_field_name === field.name);

                return {
                    model_field_name: field.name,
                    // 結合した場合、どのモデル由来か分かるように表示名を調整
                    verbose_name: field.model_source ? `${field.verbose_name} (${field.model_source})` : field.verbose_name,
                    help_text: field.help_text,
                    display_name: existingSetting?.display_name || '',
                    display_order: existingSetting?.display_order ?? (index + 1) * 10,
                    search_order: existingSetting?.search_order ?? (index + 1) * 10,
                    is_list_display: existingSetting?.is_list_display ?? true,
                    is_search_field: existingSetting?.is_search_field ?? false,
                    is_list_filter: existingSetting?.is_list_filter ?? false,
                };
            });

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
            [name]: type === 'checkbox' ? checked : value
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
            search_order: Number(item.search_order) || 0,
            is_list_display: item.is_list_display,
            is_search_field: item.is_search_field,
            is_list_filter: item.is_list_filter,
        }));

        try {
            const dataTypesToSave = selectedDataType === 'goods_receipt'
                ? ['purchase_order', 'goods_receipt']
                : [selectedDataType];

            const savePromises = dataTypesToSave.map(type =>
                fetch(`/api/base/model-display-settings/bulk-save/?data_type=${type}`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCookie('csrftoken'),
                    },
                    body: JSON.stringify(payload),
                })
            );

            const responses = await Promise.all(savePromises);

            const errorResponses = responses.filter(res => !res.ok);
            if (errorResponses.length > 0) {
                const errorResult = await errorResponses[0].json();
                console.error('Save failed:', errorResult);
                throw new Error(errorResult.message || '保存に失敗しました。');
            }

            const successResult = await responses[0].json();
            setSaveStatus({ message: successResult.message || '設定を保存しました。', variant: 'success', show: true });
            fetchAllData(selectedDataType);
        } catch (err) {
            setSaveStatus({ message: err.message, variant: 'danger', show: true });
        } finally {
            setIsSaving(false);
        }
    };

    const handleDragEnd = (result, type) => {
        if (!result.destination) {
            return;
        }
 
        const orderKey = type === 'list' ? 'display_order' : 'search_order';
        
        // The list is rendered sorted by orderKey, so we must replicate that here.
        const items = Array.from(fieldsData)
            .sort((a, b) => a[orderKey] - b[orderKey]);

        // Reorder this list based on the drag result.
        const [reorderedItem] = items.splice(result.source.index, 1);
        items.splice(result.destination.index, 0, reorderedItem);

        // Create a map of the new order for efficient lookup.
        const orderMap = new Map();
        items.forEach((item, index) => {
            orderMap.set(item.model_field_name, (index + 1) * 10);
        });

        // Update the order on the main data array, preserving the original array structure
        // and other properties.
        const newFieldsData = fieldsData.map(item => ({
            ...item,
            [orderKey]: orderMap.get(item.model_field_name)
        }));

        setFieldsData(newFieldsData);
    };

    const onDragEnd = (result) => {
        if (!result.destination) {
            return;
        }
        // droppableIdは 'list-droppable' または 'search-droppable'
        const type = result.source.droppableId === 'list-droppable' ? 'list' : 'search';
        handleDragEnd(result, type);
    };


    const renderTableRow = (item, provided, snapshot, type) => {
        const originalIndex = fieldsData.findIndex(f => f.model_field_name === item.model_field_name);
        const filterKey = type === 'list' ? 'is_list_display' : 'is_search_field';
        const isActive = item[filterKey];

        return (
            <tr
                ref={provided.innerRef}
                {...provided.draggableProps}
                className={`${snapshot.isDragging ? 'table-info' : ''} ${!isActive ? 'text-muted' : ''}`}
                style={{ ...provided.draggableProps.style, opacity: !isActive ? 0.6 : 1 }}
            >
                <td className="text-center align-middle" {...provided.dragHandleProps} style={{ cursor: 'grab' }}>
                    <span title="ドラッグして順序を変更">↕</span>
                </td>
                <td className="align-middle">
                    <OverlayTrigger placement="top" overlay={<Tooltip id={`tooltip-${type}-${originalIndex}`}>{`フィールド名: ${item.model_field_name}`}<br />{`ヘルプ: ${item.help_text || 'なし'}`}</Tooltip>}>
                        <span>{item.verbose_name}</span>
                    </OverlayTrigger>
                </td>
                <td className="align-middle">
                    <Form.Control type="text" value={item.display_name || item.verbose_name} readOnly plaintext />
                </td>
                <td className="text-center align-middle">
                    <Form.Check type="switch" id={`is_list_display-${type}-${originalIndex}`} name="is_list_display" checked={item.is_list_display} onChange={(e) => handleInputChange(originalIndex, e)} />
                </td>
                <td className="text-center align-middle">
                    <Form.Check type="switch" id={`is_search_field-${type}-${originalIndex}`} name="is_search_field" checked={item.is_search_field} onChange={(e) => handleInputChange(originalIndex, e)} />
                </td>
                <td className="text-center align-middle">
                    <Form.Check type="switch" id={`is_list_filter-${type}-${originalIndex}`} name="is_list_filter" checked={item.is_list_filter} onChange={(e) => handleInputChange(originalIndex, e)} />
                </td>
            </tr>
        );
    };

    const renderTable = (type) => {
        const orderKey = type === 'list' ? 'display_order' : 'search_order';
        const droppableId = type === 'list' ? 'list-droppable' : 'search-droppable';
        const title = type === 'list' ? '一覧表示項目' : '検索対象項目';

        // stateを直接変更しないように、配列のコピーを作成してからソートする
        const itemsToRender = [...fieldsData]
            .sort((a, b) => a[orderKey] - b[orderKey]);

        return (
            <>
                <h4>{title}</h4>
                <Table striped bordered hover responsive>
                    <thead>
                        <tr>
                            <th style={{ width: '60px' }}>順序</th>
                            <th style={{ minWidth: '120px' }}>モデル項目</th>
                            <th style={{ minWidth: '120px' }}>表示名</th>
                            <th style={{ width: '80px' }}>一覧</th>
                            <th style={{ width: '80px' }}>検索</th>
                            <th style={{ width: '80px' }}>フィルタ</th>
                        </tr>
                    </thead>
                    <Droppable droppableId={droppableId}>
                        {(provided) => (
                            <tbody {...provided.droppableProps} ref={provided.innerRef}>
                                {itemsToRender.map((item, index) => (
                                    <Draggable key={item.model_field_name} draggableId={`${type}-${item.model_field_name}`} index={index}>
                                        {(provided, snapshot) => renderTableRow(item, provided, snapshot, type)}
                                    </Draggable>
                                ))}
                                {provided.placeholder}
                            </tbody>
                        )}
                    </Droppable>
                </Table>
            </>
        );
    };

    return (
        <Container fluid className="mt-4">
            <h2>ページ項目表示設定</h2>
            <p>入庫処理ページの一覧に表示する項目や、検索・フィルタの対象をカスタマイズします。</p>

            <Row className="my-3 p-3 bg-light border rounded align-items-center">
                <Col md={4}>
                    <Form.Group>
                        <Form.Label>ページ種別</Form.Label>
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
                <DragDropContext onDragEnd={onDragEnd}>
                    <div className="mb-5">
                        {renderTable('list')}
                    </div>
                    <div>
                        {renderTable('search')}
                    </div>
                </DragDropContext>
            )}
        </Container>
    );
};

export default PageDisplaySettings;