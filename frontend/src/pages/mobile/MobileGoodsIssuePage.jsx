import React, { useState, useEffect, useCallback } from 'react';
import { Container, Form, Button, Row, Col, Card, Badge, Modal, Spinner, Alert, Pagination as BootstrapPagination } from 'react-bootstrap';
import { getCookie } from '../../utils/cookies';

const MobileGoodsIssuePage = () => {
    // State for data and UI
    const [salesOrders, setSalesOrders] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    // State for search inputs
    const [searchQueryInput, setSearchQueryInput] = useState('');
    const [searchStatusInput, setSearchStatusInput] = useState('pending');

    // State for committed search params that trigger fetch
    const [committedSearchParams, setCommittedSearchParams] = useState({ q: '', status: 'pending' });

    // State for pagination
    const [currentPage, setCurrentPage] = useState(1);
    const [totalPages, setTotalPages] = useState(0);
    const [totalCount, setTotalCount] = useState(0);
    const pageSize = 25;

    // State for modal
    const [showModal, setShowModal] = useState(false);
    const [selectedOrder, setSelectedOrder] = useState(null);
    const [quantityToShip, setQuantityToShip] = useState('');
    const [modalMessage, setModalMessage] = useState({ text: '', type: '' });
    const [isSubmitting, setIsSubmitting] = useState(false);

    const fetchSalesOrders = useCallback(async (page, query, status) => {
        setLoading(true);
        setError(null);
        
        const params = new URLSearchParams({
            page: page,
            page_size: pageSize,
        });
        if (query) params.append('search_q', query);
        if (status) params.append('search_status', status);

        try {
            const response = await fetch(`/api/inventory/sales-orders/data/?${params.toString()}`);
            if (!response.ok) {
                throw new Error('データの読み込みに失敗しました。');
            }
            const data = await response.json();
            setSalesOrders(data.results || []);
            setTotalPages(data.total_pages || 0);
            setTotalCount(data.count || 0);
        } catch (e) {
            setError(e.message);
            setSalesOrders([]);
            setTotalPages(0);
            setTotalCount(0);
        } finally {
            setLoading(false);
        }
    }, [pageSize]);

    // Effect to fetch data when page or committed search params change
    useEffect(() => {
        fetchSalesOrders(currentPage, committedSearchParams.q, committedSearchParams.status);
    }, [currentPage, committedSearchParams, fetchSalesOrders]);

    const handleSearch = (e) => {
        e.preventDefault();
        setCurrentPage(1);
        setCommittedSearchParams({ q: searchQueryInput, status: searchStatusInput });
    };

    const handleReset = () => {
        setSearchQueryInput('');
        setSearchStatusInput('pending');
        setCurrentPage(1);
        setCommittedSearchParams({ q: '', status: 'pending' });
    };

    const handleOpenModal = (order) => {
        setSelectedOrder(order);
        setQuantityToShip(order.remaining_quantity > 0 ? String(order.remaining_quantity) : '1');
        setModalMessage({ text: '', type: '' });
        setIsSubmitting(false);
        setShowModal(true);
    };

    const handleCloseModal = () => {
        setShowModal(false);
        setSelectedOrder(null);
    };

    const handleIssueSubmit = async () => {
        if (!selectedOrder) return;

        setModalMessage({ text: '', type: '' });
        const qty = parseInt(quantityToShip, 10);

        if (isNaN(qty) || qty <= 0) {
            setModalMessage({ text: '出庫数量は1以上の正の整数である必要があります。', type: 'danger' });
            return;
        }
        if (qty > selectedOrder.remaining_quantity) {
            setModalMessage({ text: '出庫数量が残数量を超えています。', type: 'danger' });
            return;
        }

        setIsSubmitting(true);

        try {
            const response = await fetch('/api/inventory/process-single-sales-order-issue/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken'),
                },
                body: JSON.stringify({
                    order_id: selectedOrder.id,
                    quantity_to_ship: qty,
                }),
            });

            const result = await response.json();

            if (response.ok && result.success) {
                setModalMessage({ text: result.message, type: 'success' });
                setTimeout(() => {
                    handleCloseModal();
                    // Re-fetch data for the current page
                    fetchSalesOrders(currentPage, committedSearchParams.q, committedSearchParams.status);
                }, 1500);
            } else {
                setModalMessage({ text: result.error || '出庫処理中にエラーが発生しました。', type: 'danger' });
            }
        } catch (err) {
            console.error('Error processing issue:', err);
            setModalMessage({ text: '通信エラーが発生しました。', type: 'danger' });
        } finally {
            setIsSubmitting(false);
        }
    };
    
    const renderPaginationInfo = () => {
        if (loading && !salesOrders.length) return '読み込み中...';
        if (error) return <span className="text-danger">エラーが発生しました</span>;
        if (totalCount === 0) return '該当する出庫予定はありません。';
        const startItem = (currentPage - 1) * pageSize + 1;
        const endItem = Math.min(startItem + pageSize - 1, totalCount);
        return `全 ${totalCount} 件中 ${startItem} - ${endItem} 件を表示 (ページ ${currentPage} / ${totalPages})`;
    };

    const renderPaginationControls = () => {
        if (totalPages <= 1) return null;
        
        let items = [];
        const startPage = Math.max(1, currentPage - 2);
        const endPage = Math.min(totalPages, currentPage + 2);

        for (let number = startPage; number <= endPage; number++) {
            items.push(
                <BootstrapPagination.Item key={number} active={number === currentPage} onClick={() => setCurrentPage(number)}>
                    {number}
                </BootstrapPagination.Item>
            );
        }

        return (
            <BootstrapPagination className="justify-content-center">
                <BootstrapPagination.Prev onClick={() => setCurrentPage(p => Math.max(1, p - 1))} disabled={currentPage === 1} />
                {items}
                <BootstrapPagination.Next onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))} disabled={currentPage === totalPages} />
            </BootstrapPagination>
        );
    };

  return (
    <Container>
        <h1 className="mb-3">出庫処理</h1>

        <div id="search-criteria-area" className="mb-3 p-3 border rounded bg-light">
            <Form onSubmit={handleSearch}>
                <Row className="g-2 mb-2">
                    <Col md={9} xs={12}>
                        <Form.Group controlId="search-q">
                            <Form.Label className="form-label-sm">検索 (受注番号/品番/倉庫):</Form.Label>
                            <Form.Control
                                type="text"
                                size="sm"
                                placeholder="受注番号, 品番, 倉庫で検索"
                                value={searchQueryInput}
                                onChange={(e) => setSearchQueryInput(e.target.value)}
                            />
                        </Form.Group>
                    </Col>
                    <Col md={3} xs={12}>
                        <Form.Group controlId="search-status">
                            <Form.Label className="form-label-sm">ステータス:</Form.Label>
                            <Form.Select
                                size="sm"
                                value={searchStatusInput}
                                onChange={(e) => setSearchStatusInput(e.target.value)}
                            >
                                <option value="">すべて</option>
                                <option value="pending">未出庫 (Pending)</option>
                                <option value="shipped">出庫済み (Shipped)</option>
                                <option value="canceled">キャンセル (Canceled)</option>
                            </Form.Select>
                        </Form.Group>
                    </Col>
                </Row>
                <Row className="g-2">
                    <Col xs={6}>
                        <Button variant="secondary" className="w-100" type="button" onClick={handleReset}>リセット</Button>
                    </Col>
                    <Col xs={6}>
                        <Button variant="primary" type="submit" className="w-100">検索</Button>
                    </Col>
                </Row>
            </Form>
        </div>

        <p className="text-muted">{renderPaginationInfo()}</p>

        <div id="sales-order-list" className="list-container">
            {loading && !salesOrders.length ? (
                <div className="text-center"><Spinner animation="border" /></div>
            ) : error ? (
                <Alert variant="danger">{error}</Alert>
            ) : salesOrders.length > 0 ? (
                salesOrders.map(order => (
                    <Card className="mb-3" key={order.id}>
                        <Card.Header className="d-flex justify-content-between align-items-center">
                            <h5 className="mb-0">{order.order_number || 'N/A'}</h5>
                            <Badge bg="info" text="dark">{order.status_display || ''}</Badge>
                        </Card.Header>
                        <Card.Body>
                            <p className="card-text mb-2">
                                <strong>品番:</strong> {order.item || 'N/A'}<br />
                                <strong>倉庫:</strong> {order.warehouse || 'N/A'}
                            </p>
                            <Row className="text-center border-top border-bottom py-2">
                                <Col>
                                    <small className="text-muted d-block">予定</small>
                                    <span className="fs-5 fw-bold">{order.quantity}</span>
                                </Col>
                                <Col>
                                    <small className="text-muted d-block">出庫済</small>
                                    <span className="fs-5 fw-bold">{order.shipped_quantity}</span>
                                </Col>
                                <Col>
                                    <small className="text-muted d-block">残</small>
                                    <span className="fs-5 fw-bold text-danger">{order.remaining_quantity}</span>
                                </Col>
                            </Row>
                            <p className="card-text mt-2 mb-0">
                                <small className="text-muted">
                                    出庫予定日: {order.expected_shipment ? new Date(order.expected_shipment).toLocaleDateString() : '未定'}
                                </small>
                            </p>
                        </Card.Body>
                        <Card.Footer className="bg-white border-0 p-2">
                            <Button
                                variant="success"
                                className="w-100"
                                onClick={() => handleOpenModal(order)}
                                disabled={order.remaining_quantity <= 0 || order.status !== 'pending'}
                            >
                                出庫処理
                            </Button>
                        </Card.Footer>
                    </Card>
                ))
            ) : (
                <Alert variant="secondary" className="text-center">データがありません。</Alert>
            )}
        </div>
        
        <div id="pagination-controls" className="d-flex justify-content-center mt-3">
            {renderPaginationControls()}
        </div>

        {/* Issue Modal */}
        <Modal show={showModal} onHide={handleCloseModal} centered>
            <Modal.Header closeButton>
                <Modal.Title>出庫処理</Modal.Title>
            </Modal.Header>
            <Modal.Body>
                {selectedOrder && (
                    <Form onSubmit={(e) => { e.preventDefault(); handleIssueSubmit(); }}>
                        <Form.Group className="mb-3">
                            <Form.Label>受注番号:</Form.Label>
                            <Form.Control type="text" defaultValue={selectedOrder.order_number} readOnly />
                        </Form.Group>
                        <Form.Group className="mb-3">
                            <Form.Label>品番:</Form.Label>
                            <Form.Control type="text" defaultValue={selectedOrder.item} readOnly />
                        </Form.Group>
                        <Form.Group className="mb-3">
                            <Form.Label>倉庫:</Form.Label>
                            <Form.Control type="text" defaultValue={selectedOrder.warehouse} readOnly />
                        </Form.Group>
                        <Form.Group className="mb-3">
                            <Form.Label>残数量:</Form.Label>
                            <Form.Control type="number" defaultValue={selectedOrder.remaining_quantity} readOnly />
                        </Form.Group>
                        <Form.Group className="mb-3">
                            <Form.Label>今回出庫数量:</Form.Label>
                            <Form.Control
                                type="number"
                                value={quantityToShip}
                                onChange={(e) => setQuantityToShip(e.target.value)}
                                min="1"
                                max={selectedOrder.remaining_quantity}
                                required
                                autoFocus
                            />
                        </Form.Group>
                    </Form>
                )}
                {modalMessage.text && (
                    <Alert variant={modalMessage.type} className="mt-3">{modalMessage.text}</Alert>
                )}
            </Modal.Body>
            <Modal.Footer className="justify-content-center gap-2">
                <Button variant="secondary" className="btn-lg flex-fill" onClick={handleCloseModal} disabled={isSubmitting}>
                    キャンセル
                </Button>
                <Button variant="primary" className="btn-lg flex-fill" onClick={handleIssueSubmit} disabled={isSubmitting}>
                    {isSubmitting ? <><Spinner as="span" animation="border" size="sm" /> 処理中...</> : '出庫実行'}
                </Button>
            </Modal.Footer>
        </Modal>
    </Container>
  );
};

export default MobileGoodsIssuePage;