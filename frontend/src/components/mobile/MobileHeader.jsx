import React from 'react';

const MobileHeader = ({ onMenuClick, isMenuOpen }) => {
  return (
    <div className="mobile-header-bar">
      <span className="mobile-header-title">モバイルアプリ</span>
      <button
        id="hamburger-menu-button"
        className="hamburger-button"
        aria-label="メニューを開閉する"
        aria-expanded={isMenuOpen}
        aria-controls="mobile-navigation-panel"
        onClick={onMenuClick}
      >
        <span className="hamburger-icon-bar"></span>
        <span className="hamburger-icon-bar"></span>
        <span className="hamburger-icon-bar"></span>
      </button>
    </div>
  );
};

export default MobileHeader;