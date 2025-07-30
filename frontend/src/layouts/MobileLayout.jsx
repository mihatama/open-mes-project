import React, { useState, useEffect } from 'react';
import { Outlet } from 'react-router-dom';
import MobileHeader from '../components/mobile/MobileHeader';
import MobileNavPanel from '../components/mobile/MobileNavPanel';
import './MobileLayout.css';

const MobileLayout = ({ onLogout }) => {
  const [isMenuOpen, setMenuOpen] = useState(false);

  const toggleMenu = () => {
    setMenuOpen(!isMenuOpen);
  };

  const closeMenu = () => {
    setMenuOpen(false);
  };

  useEffect(() => {
    if (isMenuOpen) {
      document.body.classList.add('mobile-nav-open');
    } else {
      document.body.classList.remove('mobile-nav-open');
    }
    return () => {
      document.body.classList.remove('mobile-nav-open');
    };
  }, [isMenuOpen]);

  return (
    <div className="mobile-layout">
      <header>
        <MobileHeader isMenuOpen={isMenuOpen} onMenuClick={toggleMenu} />
        <MobileNavPanel isOpen={isMenuOpen} onLinkClick={closeMenu} onLogout={onLogout} />
      </header>
      <main>
        <Outlet />
      </main>
    </div>
  );
};

export default MobileLayout;