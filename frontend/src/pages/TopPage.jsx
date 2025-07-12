import React from 'react';
import { Link } from 'react-router-dom';

const TopPage = ({ isAuthenticated, isStaffOrSuperuser }) => {
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
          <li><a href="#">生産計画</a></li>
          <li><a href="#">使用部品</a></li>
          <li><a href="#">材料引当</a></li>
          <li><a href="#">作業進捗</a></li>
        </ul>
      </div>

      <div className="menu-section">
        <h3>品質管理</h3>
        <ul>
          <li><a href="#">工程内検査</a></li>
          <li><a href="#">受入検査</a></li>
          <li><a href="#">マスター作成</a></li>
        </ul>
      </div>

      <div className="menu-section">
        <h3>設備管理</h3>
        <ul>
          <li><a href="#">始業点検</a></li>
          <li><a href="#">点検履歴</a></li>
          <li><a href="#">マスター作成</a></li>
        </ul>
      </div>

      <div className="menu-section">
        <h3>データメンテナンス</h3>
        <ul>
          <li><a href="#">データ投入</a></li>
        </ul>
      </div>

      <div className="menu-section">
        <h3>アカウント</h3>
        <ul>
          {isAuthenticated ? (
            <>
              <li><a href="#">ユーザー設定</a></li>
              {isStaffOrSuperuser && (
                <li><a href="#">ユーザー管理</a></li>
              )}
              <li>
                <form id="logout-form-top" action="#" method="post" style={{ display: 'inline' }}>
                  <button type="submit" className="link-button">ログアウト</button>
                </form>
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