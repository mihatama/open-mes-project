import React from 'react';
import { Link } from 'react-router-dom';

const MobileNavPanel = ({ isOpen, onLinkClick, onLogout }) => {
  const handleLogoutClick = (e) => {
    e.preventDefault();
    if (onLinkClick) onLinkClick(); // Close menu
    if (onLogout) onLogout();
  };

  return (
    <nav
      id="mobile-navigation-panel"
      className="mobile-navigation-panel"
      aria-hidden={!isOpen}
    >
      <ul>
        <li><Link to="/mobile" onClick={onLinkClick}>ホーム</Link></li>
        <li><Link to="/mobile/goods-receipt" onClick={onLinkClick}>入庫処理</Link></li>
        <li><Link to="/mobile/goods-issue" onClick={onLinkClick}>出庫処理</Link></li>
        <li><Link to="/mobile/location-transfer" onClick={onLinkClick}>棚番移動</Link></li>
        <li>
          <form onSubmit={handleLogoutClick}>
            <button type="submit" className="nav-link-button">ログアウト</button>
          </form>
        </li>
      </ul>
    </nav>
  );
};

export default MobileNavPanel;