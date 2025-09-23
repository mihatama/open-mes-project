import React from 'react';

const diagramStyle = {
  border: '1px solid #ddd',
  borderRadius: '5px',
  padding: '20px',
  fontFamily: 'sans-serif',
  maxWidth: '600px',
  margin: '15px 0',
  backgroundColor: '#fff',
};

const boxStyle = {
  border: '1.5px solid #495057',
  borderRadius: '5px',
  padding: '15px',
  textAlign: 'center',
  fontSize: '14px',
  fontWeight: 'bold',
  minWidth: '100px',
};

const adminBox = { ...boxStyle, backgroundColor: '#e7f5ff' };
const serverBox = { ...boxStyle, backgroundColor: '#e6f9f0' };
const userBox = { ...boxStyle, backgroundColor: '#fff9e6' };
const dbBox = { ...boxStyle, backgroundColor: '#f8f9fa', padding: '10px' };

const arrowStyle = {
  color: '#555',
  fontSize: '12px',
  textAlign: 'center',
  flexGrow: 1,
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  flexDirection: 'column',
};

const arrowSymbol = {
  fontSize: '24px',
  lineHeight: '1',
  color: '#343a40',
};

const container = {
  display: 'flex',
  justifyContent: 'space-between',
  alignItems: 'center',
  marginBottom: '30px',
};

const serverContainer = {
  display: 'flex',
  flexDirection: 'column',
  alignItems: 'center',
};

const FeatureOverviewDiagram = () => {
  return (
    <div style={diagramStyle}>
      <div style={container}>
        <div style={adminBox}>管理者</div>
        <div style={arrowStyle}>
          <span>1. 表示項目を設定</span>
          <span style={arrowSymbol}>→</span>
        </div>
        <div style={serverContainer}>
            <div style={serverBox}>サーバー</div>
            <div style={arrowStyle}>
                <span style={arrowSymbol}>↓</span>
                <span style={{marginTop: '5px'}}>2. 設定を保存</span>
            </div>
            <div style={dbBox}>DB</div>
        </div>
        <div style={arrowStyle}>
          <span>3. 設定を反映して表示</span>
          <span style={arrowSymbol}>→</span>
        </div>
        <div style={userBox}>ユーザー</div>
      </div>
    </div>
  );
};

export default FeatureOverviewDiagram;
