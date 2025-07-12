import React from 'react';
import { Link } from 'react-router-dom';

const SideMenu = ({ isOpen, isStaffOrSuperuser, onVersionClick, onLinkClick }) => {
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
      <a href="#" className="menu-subcategory-link" onClick={onLinkClick}>生産計画</a>
      <a href="#" className="menu-subcategory-link" onClick={onLinkClick}>使用部品</a>
      <a href="#" className="menu-subcategory-link" onClick={onLinkClick}>材料引当</a>
      <a href="#" className="menu-subcategory-link" onClick={onLinkClick}>作業進捗</a>

      <div className="menu-category-title">品質管理</div>
      <a href="#" className="menu-subcategory-link" onClick={onLinkClick}>工程内検査</a>
      <a href="#" className="menu-subcategory-link" onClick={onLinkClick}>受入検査</a>
      <a href="#" className="menu-subcategory-link" onClick={onLinkClick}>マスター作成</a>

      <div className="menu-category-title">設備管理</div>
      <a href="#" className="menu-subcategory-link" onClick={onLinkClick}>始業点検</a>
      <a href="#" className="menu-subcategory-link" onClick={onLinkClick}>点検履歴</a>
      <a href="#" className="menu-subcategory-link" onClick={onLinkClick}>マスター作成</a>

      <div className="menu-category-title">データメンテナンス</div>
      <a href="#" className="menu-subcategory-link" onClick={onLinkClick}>データ投入</a>

      <div className="menu-category-title">アカウント設定</div>
      <a href="#" className="menu-subcategory-link" onClick={onLinkClick}>ユーザー設定</a>
      {isStaffOrSuperuser && (
        <a href="#" className="menu-subcategory-link" onClick={onLinkClick}>ユーザー管理</a>
      )}
      <a
        href="#"
        onClick={(e) => { e.preventDefault(); onLinkClick(); onVersionClick(); }}
        className="menu-subcategory-link"
      >
        バージョン情報
      </a>
      <form id="logout-form" action="#" method="post">
        <button type="submit" className="menu-logout-button" onClick={onLinkClick}>ログアウト</button>
      </form>
    </nav>
  );
};

export default SideMenu;