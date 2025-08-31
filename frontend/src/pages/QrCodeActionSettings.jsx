import React, { useState, useEffect, useCallback } from 'react';
import { Container, Table, Button, Modal, Form, Spinner, Alert, Row, Col } from 'react-bootstrap';
import authFetch from '../utils/api';

const ACTION_TEMPLATES = {
    'モバイル入庫処理（検索）': {
        action_type: 'regex',
        description: 'QRコードから品番や発注番号を読み取り、モバイル入庫画面の検索フィールドに入力します。',
        qr_code_pattern: '(^ITEM-.+|^PO-.+)',
        script: `# QRコードのデータをモバイル入庫画面の検索クエリとして渡します。
return {
    "action": "update_search",
    "updateSearch": qr_data
}`,
        is_active: true,
    },
    'モバイル出庫処理（検索）': {
        action_type: 'regex',
        description: 'QRコードから受注番号などを読み取り、モバイル出庫画面の検索フィールドに入力します。',
        qr_code_pattern: '^SO-.+',
        script: `# QRコードのデータをモバイル出庫画面の検索クエリとして渡します。
# フロントエンド側で 'action' を見て処理を分岐させます。
return {
    "action": "update_search",
    "updateSearch": qr_data,
    "navigate": "/mobile/goods-issue"
}`,
        is_active: true,
    },
    '棚番QRコード（スクリプト判定）': {
        action_type: 'script',
        description: 'QRコードが "LOC:" で始まる場合、棚番移動画面の各フィールドを更新します。',
        qr_code_pattern: '', // スクリプト判定なので不要
        script: `# スクリプト内でQRデータの内容を判定します。
# 条件に合致しない場合は何も返しません (None)。
if qr_data.startswith("LOC:"):
    # "LOC:WAREHOUSE-A:A-01-01" のような形式を想定
    parts = qr_data.split(':')
    if len(parts) == 3:
        return {
            "action": "update_fields",
            "navigate": "/mobile/location-transfer",
            "updateFields": {
                "warehouse": parts[1],
                "sourceLocation": parts[2]
            }
        }

# 条件に合致しない場合は何も返さない
return None`,
        is_active: true,
    },
};

const QrCodeActionSettings = () => {
    const [actions, setActions] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [showModal, setShowModal] = useState(false);
    const [currentAction, setCurrentAction] = useState(null); // null for new, object for edit
    const [formErrors, setFormErrors] = useState({});
    const [isSaving, setIsSaving] = useState(false);

    const API_URL = '/api/base/qr-code-actions/';

    const fetchActions = useCallback(async () => {
        setLoading(true);
        setError(null);
        try {
            const response = await authFetch(API_URL);
            if (!response.ok) {
                throw new Error(`サーバーエラー: ${response.status}`);
            }
            const data = await response.json();
            setActions(data);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        fetchActions();
    }, [fetchActions]);

    const handleShowModal = (action = null) => {
        if (action) {
            // Editing an existing action
            setCurrentAction({ ...action });
        } else {
            // Creating a new action
            const firstTemplateName = Object.keys(ACTION_TEMPLATES)[0];
            setCurrentAction({
                name: firstTemplateName,
                action_type: 'regex', // デフォルト値
                ...ACTION_TEMPLATES[firstTemplateName],
            });
        }
        setFormErrors({});
        setShowModal(true);
    };

    const handleCloseModal = () => {
        setShowModal(false);
        setCurrentAction(null);
    };

    const handleFormChange = (e) => {
        const { name, value, type, checked } = e.target;

        // For new actions, changing the dropdown updates other fields from the template
        if (name === 'name' && !currentAction.id) {
            const template = ACTION_TEMPLATES[value];
            if (template) {
                setCurrentAction(prev => ({
                    ...prev, // Preserve is_active state
                    name: value,
                    ...template,
                    // スクリプト判定の場合、パターンをクリア
                    qr_code_pattern: template.action_type === 'script' ? '' : template.qr_code_pattern,
                }));
            }
        } else if (name === 'action_type') {
            // アクションタイプを変更した場合
            setCurrentAction(prev => ({
                ...prev,
                action_type: value,
                // スクリプト判定に切り替えたらパターンをクリア
                qr_code_pattern: value === 'script' ? '' : prev.qr_code_pattern,
            }));
        } else {
            setCurrentAction(prev => ({ ...prev, [name]: type === 'checkbox' ? checked : value }));
        }
    };

    const handleSave = async (e) => {
        e.preventDefault();
        setIsSaving(true);
        setFormErrors({});

        const isNew = !currentAction.id;
        const url = isNew ? API_URL : `${API_URL}${currentAction.id}/`;
        const method = isNew ? 'POST' : 'PUT';

        try {
            const response = await authFetch(url, {
                method: method,
                body: JSON.stringify(currentAction),
            });
            const result = await response.json();
            if (!response.ok) {
                setFormErrors(result);
                throw new Error('保存に失敗しました。入力内容を確認してください。');
            }
            handleCloseModal();
            fetchActions();
        } catch (err) {
            setFormErrors(prev => ({ ...prev, non_field_errors: err.message }));
        } finally {
            setIsSaving(false);
        }
    };

    const handleDelete = async (id) => {
        if (window.confirm('このアクションを本当に削除しますか？')) {
            try {
                const response = await authFetch(`${API_URL}${id}/`, {
                    method: 'DELETE',
                });
                if (!response.ok) {
                    throw new Error('削除に失敗しました。');
                }
                fetchActions();
            } catch (err) {
                setError(err.message);
            }
        }
    };

    return (
        <Container fluid className="mt-4">
            <Row className="align-items-center mb-3">
                <Col>
                    <h2>QRコードアクション設定</h2>
                    <p>QRコードを読み取った際の動作を定義します。正規表現にマッチした最初の有効なアクションが実行されます。</p>
                </Col>
                <Col xs="auto">
                    <Button variant="primary" onClick={() => handleShowModal()}>新規作成</Button>
                </Col>
            </Row>

            {loading && <Spinner animation="border" />}
            {error && <Alert variant="danger">{error}</Alert>}

            {!loading && !error && (
                <Table striped bordered hover responsive>
                    <thead>
                        <tr>
                            <th>アクション名</th>
                            <th>QRコードパターン (正規表現)</th>
                            <th>説明</th>
                            <th className="text-center">有効</th>
                            <th className="text-center">操作</th>
                        </tr>
                    </thead>
                    <tbody>
                        {actions.map(action => (
                            <tr key={action.id}>
                                <td>{action.name}</td>
                                <td><code>{action.qr_code_pattern}</code></td>
                                <td>{action.description}</td>
                                <td className="text-center">{action.is_active ? '✔️' : '❌'}</td>
                                <td className="text-center">
                                    <Button variant="info" size="sm" onClick={() => handleShowModal(action)}>編集</Button>
                                    <Button variant="danger" size="sm" className="ms-2" onClick={() => handleDelete(action.id)}>削除</Button>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </Table>
            )}

            {currentAction &&
                <Modal show={showModal} onHide={handleCloseModal} size="lg" backdrop="static" centered>
                    <Form onSubmit={handleSave}>
                        <Modal.Header closeButton>
                            <Modal.Title>{currentAction.id ? 'アクションの編集' : '新規アクションの作成'}</Modal.Title>
                        </Modal.Header>
                        <Modal.Body>
                            {formErrors.non_field_errors && <Alert variant="danger">{formErrors.non_field_errors}</Alert>}

                            <Form.Group as={Row} className="mb-3" controlId="formAction">
                                <Form.Label column sm={3}>{currentAction.id ? 'アクション名' : 'アクション'}</Form.Label>
                                <Col sm={9}>
                                    {currentAction.id ? (
                                        <Form.Control plaintext readOnly value={currentAction.name} />
                                    ) : (
                                        <Form.Select name="name" value={currentAction.name} onChange={handleFormChange} isInvalid={!!formErrors.name} required>
                                            {Object.keys(ACTION_TEMPLATES).map(templateName => (
                                                <option key={templateName} value={templateName}>{templateName}</option>
                                            ))}
                                        </Form.Select>
                                    )}
                                    <Form.Control.Feedback type="invalid">{formErrors.name}</Form.Control.Feedback>
                                </Col>
                            </Form.Group>

                            <Form.Group as={Row} className="mb-3" controlId="formActionType">
                                <Form.Label column sm={3}>アクションタイプ</Form.Label>
                                <Col sm={9} className="d-flex align-items-center">
                                    <Form.Check
                                        inline
                                        type="radio"
                                        label="正規表現で判定"
                                        name="action_type"
                                        id="action_type_regex"
                                        value="regex"
                                        checked={currentAction.action_type === 'regex'}
                                        onChange={handleFormChange}
                                    />
                                    <Form.Check
                                        inline
                                        type="radio"
                                        label="スクリプトで判定"
                                        name="action_type"
                                        id="action_type_script"
                                        value="script"
                                        checked={currentAction.action_type === 'script'}
                                        onChange={handleFormChange}
                                    />
                                </Col>
                            </Form.Group>

                            <Form.Group as={Row} className="mb-3" controlId="formDescription">
                                <Form.Label column sm={3}>説明</Form.Label>
                                <Col sm={9}>
                                    <Form.Control as="textarea" rows={2} name="description" value={currentAction.description} onChange={handleFormChange} isInvalid={!!formErrors.description} />
                                    <Form.Control.Feedback type="invalid">{formErrors.description}</Form.Control.Feedback>
                                </Col>
                            </Form.Group>

                            {currentAction.action_type === 'regex' && (
                                <Form.Group as={Row} className="mb-3" controlId="formPattern">
                                    <Form.Label column sm={3}>QRコードパターン</Form.Label>
                                    <Col sm={9}>
                                        <Form.Control type="text" name="qr_code_pattern" value={currentAction.qr_code_pattern} onChange={handleFormChange} isInvalid={!!formErrors.qr_code_pattern} required />
                                        <Form.Text className="text-muted">マッチング対象のQRコードの正規表現パターン。例: ^ITEM-.+</Form.Text>
                                        <Form.Control.Feedback type="invalid">{formErrors.qr_code_pattern}</Form.Control.Feedback>
                                    </Col>
                                </Form.Group>
                            )}
                            {currentAction.action_type === 'script' && (
                                <Form.Group className="mb-3" controlId="formScript">
                                    <Form.Label>実行スクリプト (Python)</Form.Label>
                                    <Form.Text className="text-muted d-block mb-2">
                                        スクリプト内でQRデータの内容を判定し、条件に合致すれば処理内容を辞書として<code>return</code>してください。合致しない場合は<code>None</code>を返してください。
                                    </Form.Text>
                                    <Form.Control
                                        as="textarea"
                                        rows={10}
                                        name="script"
                                        value={currentAction.script}
                                        onChange={handleFormChange}
                                        isInvalid={!!formErrors.script}
                                        required
                                        style={{ fontFamily: 'monospace', fontSize: '0.9rem' }}
                                    />
                                    <Form.Control.Feedback type="invalid">{formErrors.script}</Form.Control.Feedback>
                                </Form.Group>
                            )}
                            <Form.Group className="mb-3" controlId="formIsActive">
                                <Form.Check type="switch" name="is_active" label="このアクションを有効にする" checked={currentAction.is_active} onChange={handleFormChange} />
                            </Form.Group>
                        </Modal.Body>
                        <Modal.Footer>
                            <Button variant="secondary" onClick={handleCloseModal}>キャンセル</Button>
                            <Button variant="primary" type="submit" disabled={isSaving}>
                                {isSaving ? <><Spinner as="span" animation="border" size="sm" /> 保存中...</> : '保存'}
                            </Button>
                        </Modal.Footer>
                    </Form>
                </Modal>}
        </Container>
    );
};

export default QrCodeActionSettings;