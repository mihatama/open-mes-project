import React from 'react';

const diagramStyle = {
  border: '2px solid #ced4da',
  borderRadius: '5px',
  padding: '20px',
  fontFamily: 'sans-serif',
  maxWidth: '600px',
  margin: '15px 0',
};

const titleStyle = {
  fontSize: '20px',
  fontWeight: 'bold',
  textAlign: 'center',
  marginBottom: '20px',
};

const areaStyle = {
  border: '1.5px dashed #adb5bd',
  borderRadius: '5px',
  padding: '20px',
  margin: '15px 0',
  textAlign: 'center',
  fontSize: '16px',
  fontWeight: 'bold',
  color: '#495057',
  backgroundColor: '#f8f9fa',
};

const InventoryInquiryLayoutDiagram = () => {
  return (
    <div style={diagramStyle}>
      <div style={titleStyle}>在庫照会画面</div>

      <div style={areaStyle}>① 検索エリア</div>

      <div style={areaStyle}>② 在庫一覧エリア</div>

      <div style={areaStyle}>③ ページネーションエリア</div>
    </div>
  );
};

export default InventoryInquiryLayoutDiagram;
