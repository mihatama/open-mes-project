import React from 'react';
import { Link } from 'react-router-dom';
import './MobileTopPage.css';

const MobileTopPage = () => {
  return (
    <div className="mobile-top-page-container">
      <h1>ようこそ！</h1>
      <p>これはモバイル向けのページです。</p>
      <div className="button-container">
        <Link to="/mobile/goods-receipt" className="action-button">入庫処理</Link>
        <Link to="/mobile/goods-issue" className="action-button">出庫処理</Link>
        <Link to="/mobile/location-transfer" className="action-button">棚番移動</Link>
      </div>
    </div>
  );
};

export default MobileTopPage;