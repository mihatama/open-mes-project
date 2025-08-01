import React, { useState, useEffect, useCallback } from 'react';
import { Container, Table, Button, Form, Spinner, Alert, Row, Col, Tooltip, OverlayTrigger } from 'react-bootstrap';
import { DragDropContext, Droppable, Draggable } from '@hello-pangea/dnd';
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
    const [combinedData, setCombinedData] = useState([]);
    const [selectedDataType, setSelectedDataType] = useState(DATA_TYPE_CHOICES[0].value);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [saveStatus, setSaveStatus] = useState({ message: '', variant: '', show: false });

    const fetchAllData = useCallback(async (dataType) => {
        setLoading(true);
        setError(null);
        setSaveStatus(prev => ({ ...prev, show: false }));
        try {
            const [mappingsRes, fieldsRes, displaySettingsRes] = await Promise.all([
                fetch(`/api/base/csv-mappings/?data_type=${dataType}`),
                fetch(`/api/base/model-fields/?data_type=${dataType}`),
                fetch(`/api/base/model-display-settings/?data_type=${dataType}`)
            ]);

            if (!mappingsRes.ok) throw new Error(`既存マッピングの取得に失敗しました: ${mappingsRes.statusText}`);
            if (!fieldsRes.ok) throw new Error(`モデル情報の取得に失敗しました: ${fieldsRes.statusText}`);
            if (!displaySettingsRes.ok) throw new Error(`表示設定の取得に失敗しました: ${displaySettingsRes.statusText}`);

            const mappings = await mappingsRes.json();
            const modelFields = await fieldsRes.json();
            const displaySettings = await displaySettingsRes.json();

            const data = modelFields
                .filter(field => field.name !== 'id') // 'id'フィールドはマッピング対象外とする
                .map((field, index) => {
                const existingMapping = mappings.find(m => m.model_field_name === field.name);
                const displaySetting = displaySettings.find(s => s.model_field_name === field.name);
                const isActive = !!existingMapping;

                return {
                    // Model field info (read-only)
                    model_field_name: field.name,
                    verbose_name: field.verbose_name,
                    is_model_required: field.is_required,
                    default_value: field.default_value,
                    help_text: field.help_text,
                    // Mapping info (editable)
                    csv_header: existingMapping?.csv_header || '',
                    custom_display_name: displaySetting?.display_name || '', // モデル表示設定のカスタム名を取得
                    order: existingMapping?.order || (index + 1) * 10,
                    is_update_key: existingMapping ? existingMapping.is_update_key : false,
                    is_active: isActive,
                };
            });

            data.sort((a, b) => a.order - b.order);
            setCombinedData(data);

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
        const newCombinedData = [...combinedData];
        newCombinedData[index] = {
            ...newCombinedData[index],
            [name]: type === 'checkbox' ? checked : value
        };
        setCombinedData(newCombinedData);
    };

    const handleSave = async () => {
        setLoading(true);
        setSaveStatus({ message: '', variant: '', show: false });

        const payload = combinedData.map(item => ({
            model_field_name: item.model_field_name,
            csv_header: item.csv_header,
            custom_display_name: item.custom_display_name,
            order: Number(item.order) || 0,
            is_update_key: item.is_update_key,
            is_active: item.is_active,
        }));

        try {
            const response = await fetch(`/api/base/csv-mappings/bulk-save/?data_type=${selectedDataType}`, {
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
            // 再取得して画面を最新化
            fetchAllData(selectedDataType);
        } catch (err) {
            setSaveStatus({ message: err.message, variant: 'danger', show: true });
        } finally {
            setLoading(false);
        }
    };

    const handleDragEnd = (result) => {
        if (!result.destination) {
            return;
        }

        const items = Array.from(combinedData);
        const [reorderedItem] = items.splice(result.source.index, 1);
        items.splice(result.destination.index, 0, reorderedItem);

        // 新しい順序に基づいて 'order' プロパティを更新
        const updatedItems = items.map((item, index) => ({
            ...item,
            order: (index + 1) * 10, // 10, 20, 30... のように再採番
        }));

        setCombinedData(updatedItems);
    };

    return (
        <Container fluid className="mt-4">
            <h2>CSVマッピング設定</h2>
            <p>CSVインポート時の列（ヘッダー）とシステムの項目を紐付けます。モデルの各項目に対して、CSVファイルのどの列を割り当てるかを設定してください。</p>

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
                    <Button variant="primary" onClick={handleSave} disabled={loading}>
                        {loading ? <><Spinner as="span" animation="border" size="sm" role="status" aria-hidden="true" /> 保存中...</> : 'この設定で保存'}
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
                                <th style={{ width: '60px' }}></th>
                                <th style={{ minWidth: '80px' }}>有効</th>
                                <th style={{ minWidth: '180px' }}>モデル項目</th>
                                <th style={{ minWidth: '200px' }}>カスタム表示名</th>
                                <th style={{ minWidth: '200px' }}>CSVヘッダー名</th>
                                <th style={{ minWidth: '120px' }}>上書きキー</th>
                            </tr>
                        </thead>
                        <Droppable droppableId="csv-mapping-droppable">
                            {(provided) => (
                                <tbody {...provided.droppableProps} ref={provided.innerRef}>
                                    {combinedData.map((item, index) => (
                                        <Draggable key={item.model_field_name} draggableId={item.model_field_name} index={index}>
                                            {(provided, snapshot) => (
                                                <tr
                                                    ref={provided.innerRef}
                                                    {...provided.draggableProps}
                                                    className={`${!item.is_active ? 'text-muted' : ''} ${snapshot.isDragging ? 'table-info' : ''}`}
                                                    style={{ ...provided.draggableProps.style }}
                                                >
                                                    <td className="text-center align-middle" {...provided.dragHandleProps} style={{ cursor: 'grab' }}>
                                                        <span title="ドラッグして順序を変更">↕</span>
                                                    </td>
                                                    <td className="text-center align-middle">
                                                        <Form.Check type="switch" id={`is_active-${index}`} name="is_active" checked={item.is_active} onChange={(e) => handleInputChange(index, e)} />
                                                    </td>
                                                    <td className="align-middle">
                                                        <OverlayTrigger placement="top" overlay={<Tooltip id={`tooltip-${index}`}>{`フィールド名: ${item.model_field_name}`}<br />{`必須(モデル): ${item.is_model_required ? 'はい' : 'いいえ'}`}<br />{`デフォルト値: ${item.default_value || 'なし'}`}<br />{`ヘルプ: ${item.help_text || 'なし'}`}</Tooltip>}>
                                                            <span>{item.verbose_name}</span>
                                                        </OverlayTrigger>
                                                    </td>
                                                    <td className="align-middle">
                                                        {item.custom_display_name || item.verbose_name}
                                                    </td>
                                                    <td className="align-middle">
                                                        <Form.Control type="text" name="csv_header" value={item.csv_header} onChange={(e) => handleInputChange(index, e)} disabled={!item.is_active} />
                                                    </td>
                                                    <td className="text-center align-middle">
                                                        <OverlayTrigger placement="top" overlay={<Tooltip>インポート時にこの項目を使って既存のデータを検索し、上書きします。</Tooltip>}>
                                                            <Form.Check type="checkbox" id={`is_update_key-${index}`} name="is_update_key" checked={item.is_update_key} onChange={(e) => handleInputChange(index, e)} disabled={!item.is_active} />
                                                        </OverlayTrigger>
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

export default CsvMappingSettings;