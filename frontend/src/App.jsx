import { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import './App.css';
import Header from './components/Header.jsx';
import SideMenu from './components/SideMenu.jsx';
import VersionModal from './components/VersionModal.jsx';
import TopPage from './pages/TopPage.jsx';
import InventoryInquiry from './pages/InventoryInquiry.jsx';
import StockMovementHistory from './pages/StockMovementHistory.jsx';
import ShipmentSchedule from './pages/ShipmentSchedule.jsx';
import GoodsReceipt from './pages/GoodsReceipt.jsx';
import GoodsIssue from './pages/GoodsIssue.jsx';

function App() {
  // TODO: Replace with actual authentication state
  const isAuthenticated = true;
  const isStaffOrSuperuser = true;
  const [isMenuOpen, setMenuOpen] = useState(false);
  const [isVersionModalOpen, setVersionModalOpen] = useState(false);

  const toggleMenu = () => {
    setMenuOpen(!isMenuOpen);
  };

  useEffect(() => {
    // Add or remove class from body to prevent scrolling when menu is open
    if (isMenuOpen) {
      document.body.classList.add('menu-open-no-scroll');
    } else {
      document.body.classList.remove('menu-open-no-scroll');
    }

    // Cleanup function to remove the class when the component unmounts
    return () => {
      document.body.classList.remove('menu-open-no-scroll');
    };
  }, [isMenuOpen]);

  return (
    <Router>
      <Header onMenuClick={toggleMenu} isMenuOpen={isMenuOpen} isAuthenticated={isAuthenticated} />
      {isAuthenticated && (
        <>
          <SideMenu
            isOpen={isMenuOpen}
            isStaffOrSuperuser={isStaffOrSuperuser}
            onVersionClick={() => setVersionModalOpen(true)}
          />
          {isMenuOpen && <div id="menu-overlay" onClick={toggleMenu}></div>}
        </>
      )}
      <div className="container">
        <main className="main-contents">
          <Routes>
            <Route path="/" element={<TopPage isAuthenticated={isAuthenticated} isStaffOrSuperuser={isStaffOrSuperuser} />} />
            {/* Inventory Management */}
            <Route path="/inventory/inquiry" element={<InventoryInquiry />} />
            <Route path="/inventory/stock-movement-history" element={<StockMovementHistory />} />
            <Route path="/inventory/shipment" element={<ShipmentSchedule />} />
            <Route path="/inventory/purchase" element={<GoodsReceipt />} />
            <Route path="/inventory/issue" element={<GoodsIssue />} />
            {/* TODO: Add routes for other pages */}
          </Routes>
        </main>
      </div>
      <VersionModal isOpen={isVersionModalOpen} onClose={() => setVersionModalOpen(false)} />
    </Router>
  )
}

export default App
