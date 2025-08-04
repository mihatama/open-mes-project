import React from 'react';
import { Link } from 'react-router-dom';

const SideMenu = ({ isOpen, isStaffOrSuperuser, onVersionClick, onLinkClick, onLogout }) => {
  const handleLogoutClick = (e) => {
    e.preventDefault();
    onLinkClick(); // Close menu on click
    onLogout();
  };

  return (
    <nav id="menu-bar" className={isOpen ? 'open' : ''}>
      <Link to="/" onClick={onLinkClick}>トップページ</Link>
      <div className="menu-category-title">在庫管理</div>
      <Link to="/inventory/inquiry" className="menu-subcategory-link" onClick={onLinkClick}>在庫照会</Link>
      <Link to="/inventory/stock-movement-history" className="menu-subcategory-link" onClick={onLinkClick}>入出庫履歴</Link>
      <Link to="/inventory/shipment" className="menu-subcategory-link" onClick={onLinkClick}>出庫予定</Link>
      <Link to="/inventory/purchase" className="menu-subcategory-link" onClick={onLinkClick}>入庫処置</Link>
      <Link to="/inventory/issue" className="menu-subcategory-link" onClick={onLinkClick}>出庫処理</Link>

      <div className="menu-category-title">生産管理</div>
      <Link to="/production/plan" className="menu-subcategory-link" onClick={onLinkClick}>生産計画</Link>
      <Link to="/production/parts-used" className="menu-subcategory-link" onClick={onLinkClick}>使用部品</Link>
      <Link to="/production/material-allocation" className="menu-subcategory-link" onClick={onLinkClick}>材料引当</Link>
      <Link to="/production/work-progress" className="menu-subcategory-link" onClick={onLinkClick}>作業進捗</Link>

      <div className="menu-category-title">品質管理</div>
      <Link to="/quality/process-inspection" className="menu-subcategory-link" onClick={onLinkClick}>工程内検査</Link>
      <Link to="/quality/acceptance-inspection" className="menu-subcategory-link" onClick={onLinkClick}>受入検査</Link>
      <Link to="/quality/master-creation" className="menu-subcategory-link" onClick={onLinkClick}>マスター作成</Link>

      <div className="menu-category-title">設備管理</div>
      <Link to="/machine/start-inspection" className="menu-subcategory-link" onClick={onLinkClick}>始業点検</Link>
      <Link to="/machine/inspection-history" className="menu-subcategory-link" onClick={onLinkClick}>点検履歴</Link>
      <Link to="/machine/master-creation" className="menu-subcategory-link" onClick={onLinkClick}>マスター作成</Link>

      <div className="menu-category-title">データメンテナンス</div>
      <Link to="/data/import" className="menu-subcategory-link" onClick={onLinkClick}>データ投入</Link>

      {isStaffOrSuperuser && (
        <>
          <div className="menu-category-title">管理者メニュー</div>
          <Link to="/system/settings" className="menu-subcategory-link" onClick={onLinkClick}>システム設定</Link>
          <Link to="/user/management" className="menu-subcategory-link" onClick={onLinkClick}>ユーザー管理</Link>
          <Link to="/system/qr-code-actions" className="menu-subcategory-link" onClick={onLinkClick}>QRコードアクション設定</Link>
        </>
      )}

      <div className="menu-category-title">アカウント設定</div>
      <Link to="/user/settings" className="menu-subcategory-link" onClick={onLinkClick}>ユーザー設定</Link>
      <a
        href="#"
        onClick={(e) => { e.preventDefault(); onLinkClick(); onVersionClick(); }}
        className="menu-subcategory-link"
      >
        バージョン情報
      </a>
      <button onClick={handleLogoutClick} className="menu-logout-button">ログアウト</button>
    </nav>
  );
};

export default SideMenu;