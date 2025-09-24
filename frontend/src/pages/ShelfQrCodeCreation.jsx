import React, { useState } from 'react';
import { QRCodeCanvas } from 'qrcode.react';
import { Card, Form, Container, Row, Col, Button } from 'react-bootstrap';

const ShelfQrCodeCreation = () => {
  const [warehouse, setWarehouse] = useState('');
  const [shelf, setShelf] = useState('');

  const qrCodeValue = JSON.stringify({ warehouse, shelf });

  const handleDownload = () => {
    const canvas = document.getElementById('qr-code-canvas');
    if (canvas) {
      const pngUrl = canvas
        .toDataURL('image/png')
        .replace('image/png', 'image/octet-stream');
      const downloadLink = document.createElement('a');
      downloadLink.href = pngUrl;
      downloadLink.download = `${warehouse || 'W'}-${shelf || 'S'}-qrcode.png`;
      document.body.appendChild(downloadLink);
      downloadLink.click();
      document.body.removeChild(downloadLink);
    }
  };

  return (
    <Container className="mt-4">
      <Row className="justify-content-md-center">
        <Col md={6}>
          <Card>
            <Card.Body>
              <Card.Title as="h2" className="text-center mb-4">倉庫棚番QR作成</Card.Title>
              <Form>
                <Form.Group as={Row} className="mb-3" controlId="warehouse-input">
                  <Form.Label column sm={3}>
                    倉庫番号
                  </Form.Label>
                  <Col sm={9}>
                    <Form.Control
                      type="text"
                      value={warehouse}
                      onChange={(e) => setWarehouse(e.target.value)}
                      placeholder="倉庫番号を入力"
                    />
                  </Col>
                </Form.Group>

                <Form.Group as={Row} className="mb-3" controlId="shelf-input">
                  <Form.Label column sm={3}>
                    棚番号
                  </Form.Label>
                  <Col sm={9}>
                    <Form.Control
                      type="text"
                      value={shelf}
                      onChange={(e) => setShelf(e.target.value)}
                      placeholder="棚番号を入力"
                    />
                  </Col>
                </Form.Group>
              </Form>

              {warehouse && shelf && (
                <div className="text-center mt-4">
                  <h4>生成されたQRコード</h4>
                  <div className="d-inline-block p-3 border rounded">
                    <QRCodeCanvas id="qr-code-canvas" value={qrCodeValue} size={256} />
                  </div>
                  <p className="mt-3">QRコードの文字列:</p>
                  <code>{qrCodeValue}</code>
                  <div className="mt-3">
                    <Button variant="primary" onClick={handleDownload}>
                      PNGでダウンロード
                    </Button>
                  </div>
                </div>
              )}
            </Card.Body>
          </Card>
        </Col>
      </Row>
    </Container>
  );
};

export default ShelfQrCodeCreation;