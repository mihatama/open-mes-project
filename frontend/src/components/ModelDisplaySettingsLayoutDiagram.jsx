import React from 'react';

const diagramStyle = {
  border: '2px solid #ced4da',
  borderRadius: '5px',
  padding: '20px',
  fontFamily: 'sans-serif',
  maxWidth: '700px',
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

const tableMockStyle = {
  marginTop: '20px',
  fontSize: '12px',
  color: '#6c757d',
  fontStyle: 'italic',
  textAlign: 'left',
};

const ModelDisplaySettingsLayoutDiagram = () => {
  return (
    <div style={diagramStyle}>
      <div style={titleStyle}>ページ項目表示設定</div>

      <div style={areaStyle}>① データ種別選択</div>

      <div style={areaStyle}>
        ② 設定テーブル
        <div style={tableMockStyle}>
          <p style={{ margin: '5px 0' }}>・「↕」をドラッグ&ドロップで順序変更</p>
          <p style={{ margin: '5px 0' }}>・「カスタム表示名」を入力</p>
          <p style={{ margin: '5px 0' }}>・「一覧表示」「検索対象」のスイッチをON/OFF</p>
        </div>
      </div>

      <div style={areaStyle}>③ 保存ボタン</div>
    </div>
  );
};

export default ModelDisplaySettingsLayoutDiagram;
