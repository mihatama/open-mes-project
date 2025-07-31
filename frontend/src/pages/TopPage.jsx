import React from 'react';
import { Link } from 'react-router-dom';

const TopPage = ({ isAuthenticated, isStaffOrSuperuser, onLogout }) => {
  return (
    <div className="top-page-container">
      <div className="menu-section">
        <h3>在庫管理</h3>
        <ul>
          <li><Link to="/inventory/inquiry">在庫照会</Link></li>
          <li><Link to="/inventory/stock-movement-history">入出庫履歴</Link></li>
          <li><Link to="/inventory/shipment">出庫予定</Link></li>
          <li><Link to="/inventory/purchase">入庫処置</Link></li>
          <li><Link to="/inventory/issue">出庫処理</Link></li>
        </ul>
      </div>

      <div className="menu-section">
        <h3>生産管理</h3>
        <ul>
          <li><Link to="/production/plan">生産計画</Link></li>
          <li><Link to="/production/parts-used">使用部品</Link></li>
          <li><Link to="/production/material-allocation">材料引当</Link></li>
          <li><Link to="/production/work-progress">作業進捗</Link></li>
        </ul>
      </div>

      <div className="menu-section">
        <h3>品質管理</h3>
        <ul>
          <li><Link to="/quality/process-inspection">工程内検査</Link></li>
          <li><Link to="/quality/acceptance-inspection">受入検査</Link></li>
          <li><Link to="/quality/master-creation">マスター作成</Link></li>
        </ul>
      </div>

      <div className="menu-section">
        <h3>設備管理</h3>
        <ul>
          <li><Link to="/machine/start-inspection">始業点検</Link></li>
          <li><Link to="/machine/inspection-history">点検履歴</Link></li>
          <li><Link to="/machine/master-creation">マスター作成</Link></li>
        </ul>
      </div>

      <div className="menu-section">
        <h3>データメンテナンス</h3>
        <ul>
          <li><Link to="/data/import">データ投入</Link></li>
        </ul>
      </div>

      {isStaffOrSuperuser && (
        <div className="menu-section">
          <h3>管理者メニュー</h3>
          <ul>
            <li><Link to="/user/management">ユーザー管理</Link></li>
            <li><Link to="/system/settings">システム設定</Link></li>
          </ul>
        </div>
      )}

      <div className="menu-section">
        <h3>アカウント</h3>
        <ul>
          {isAuthenticated ? (
            <>
              <li><Link to="/user/settings">ユーザー設定</Link></li>
              <li>
                <button type="button" onClick={onLogout} className="link-button">ログアウト</button>
              </li>
            </>
          ) : (
            <li><a href="#">ログイン</a></li>
          )}
        </ul>
      </div>
    </div>
  );
};

export default TopPage;