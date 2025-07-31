import React from 'react';
import { Link } from 'react-router-dom';
import { Card, ListGroup } from 'react-bootstrap';

const SystemSettings = () => {
  return (
    <div>
      <h2>システム設定</h2>
      <p>このページでは、システム全体の動作に関わる設定を管理します。</p>
      <Card style={{ width: '24rem', marginTop: '2rem' }}>
        <Card.Header as="h5">設定項目</Card.Header>
        <ListGroup variant="flush">
          <ListGroup.Item action as={Link} to="/system/csv-mappings">CSVマッピング設定</ListGroup.Item>
        </ListGroup>
      </Card>
    </div>
  );
};

export default SystemSettings;