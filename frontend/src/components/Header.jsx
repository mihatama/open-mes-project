import React from 'react';

const Header = ({ onMenuClick, isMenuOpen, isAuthenticated }) => {
  return (
    <header>
      {isAuthenticated && (
        <div
          id="hamburger-menu"
          className={isMenuOpen ? 'open' : ''}
          onClick={onMenuClick}
        >
          <span></span>
          <span></span>
          <span></span>
        </div>
      )}
      <h1 id="title">みんなのMES</h1>
    </header>
  );
};

export default Header;