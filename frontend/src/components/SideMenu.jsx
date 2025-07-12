import React from 'react';

const SideMenu = ({ isOpen, isStaffOrSuperuser, onVersionClick }) => {
  return (
    <nav id="menu-bar" className={isOpen ? 'open' : ''}>
      <a href="#">トップページ</a>
      <div className="menu-category-title">在庫管理</div>
      <a href="#" className="menu-subcategory-link">在庫照会</a>
      <a href="#" className="menu-subcategory-link">入出庫履歴</a>
      <a href="#" className="menu-subcategory-link">出庫予定</a>
      <a href="#" className="menu-subcategory-link">入庫処置</a>
      <a href="#" className="menu-subcategory-link">出庫処理</a>

      <div className="menu-category-title">生産管理</div>
      <a href="#" className="menu-subcategory-link">生産計画</a>
      <a href="#" className="menu-subcategory-link">使用部品</a>
      <a href="#" className="menu-subcategory-link">材料引当</a>
      <a href="#" className="menu-subcategory-link">作業進捗</a>

      <div className="menu-category-title">品質管理</div>
      <a href="#" className="menu-subcategory-link">工程内検査</a>
      <a href="#" className="menu-subcategory-link">受入検査</a>
      <a href="#" className="menu-subcategory-link">マスター作成</a>

      <div className="menu-category-title">設備管理</div>
      <a href="#" className="menu-subcategory-link">始業点検</a>
      <a href="#" className="menu-subcategory-link">点検履歴</a>
      <a href="#" className="menu-subcategory-link">マスター作成</a>

      <div className="menu-category-title">データメンテナンス</div>
      <a href="#" className="menu-subcategory-link">データ投入</a>

      <div className="menu-category-title">アカウント設定</div>
      <a href="#" className="menu-subcategory-link">ユーザー設定</a>
      {isStaffOrSuperuser && (
        <a href="#" className="menu-subcategory-link">ユーザー管理</a>
      )}
      <a
        href="#"
        onClick={(e) => { e.preventDefault(); onVersionClick(); }}
        className="menu-subcategory-link"
      >
        バージョン情報
      </a>
      <form id="logout-form" action="#" method="post">
        <button type="submit" className="menu-logout-button">ログアウト</button>
      </form>
    </nav>
  );
};

export default SideMenu;