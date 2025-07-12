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
import ProductionPlan from './pages/ProductionPlan.jsx';
import PartsUsed from './pages/PartsUsed.jsx';
import MaterialAllocation from './pages/MaterialAllocation.jsx';
import WorkProgress from './pages/WorkProgress.jsx';
import ProcessInspection from './pages/ProcessInspection.jsx';
import AcceptanceInspection from './pages/AcceptanceInspection.jsx';
import QualityMasterCreation from './pages/QualityMasterCreation.jsx';
import StartInspection from './pages/StartInspection.jsx';
import InspectionHistory from './pages/InspectionHistory.jsx';
import MachineMasterCreation from './pages/MachineMasterCreation.jsx';
import DataImport from './pages/DataImport.jsx';
import UserSettings from './pages/UserSettings.jsx';
import UserManagement from './pages/UserManagement.jsx';

function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== '') {
    const cookies = document.cookie.split(';');
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      if (cookie.substring(0, name.length + 1) === (name + '=')) {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isStaffOrSuperuser, setIsStaffOrSuperuser] = useState(false);
  const [isMenuOpen, setMenuOpen] = useState(false);
  const [isVersionModalOpen, setVersionModalOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(true); // ローディング状態を追加

  useEffect(() => {
    // アプリケーションのロード時にセッション情報を確認し、CSRFトークンを取得
    const checkAuthStatus = async () => {
      try {
        const response = await fetch('/api/users/session/');
        if (response.ok) {
          const data = await response.json();
          setIsAuthenticated(data.isAuthenticated);
          setIsStaffOrSuperuser(data.isStaff || data.isSuperuser);
        } else {
          // ログインページにリダイレクト、または認証されていない状態として続行
          setIsAuthenticated(false);
          setIsStaffOrSuperuser(false);
        }
      } catch (error) {
        console.error('Authentication check failed:', error);
        setIsAuthenticated(false);
        setIsStaffOrSuperuser(false);
      } finally {
        setIsLoading(false); // ローディング完了
      }
    };

    checkAuthStatus();
  }, []); // 空の依存配列で、コンポーネントのマウント時に一度だけ実行

  const handleLogout = async () => {
    const csrfToken = getCookie('csrftoken');
    const response = await fetch('/api/users/logout/', {
      method: 'POST',
      headers: {
        'X-CSRFToken': csrfToken,
      },
    });

    if (response.ok) {
      window.location.href = '/'; // Redirect to home and reload
    } else {
      // エラー時にもう少し詳しい情報を表示
      const data = await response.json().catch(() => ({}));
      alert(`Logout failed: ${data.message || 'Server error'}`);
    }
  };

  const toggleMenu = () => {
    setMenuOpen(!isMenuOpen);
  };

  const closeMenu = () => {
    setMenuOpen(false);
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

  if (isLoading) {
    return <div>Loading...</div>; // またはスピナーなどを表示
  }

  return (
    <Router>
      <Header onMenuClick={toggleMenu} isMenuOpen={isMenuOpen} isAuthenticated={isAuthenticated} />
      {isAuthenticated && (
        <>
          <SideMenu
            isOpen={isMenuOpen}
            isStaffOrSuperuser={isStaffOrSuperuser}
            onVersionClick={() => setVersionModalOpen(true)}
            onLinkClick={closeMenu}
            onLogout={handleLogout}
          />
          {isMenuOpen && <div id="menu-overlay" onClick={toggleMenu}></div>}
        </>
      )}
      <div className="container">
        <main className="main-contents">
          <Routes>
            <Route path="/" element={<TopPage isAuthenticated={isAuthenticated} isStaffOrSuperuser={isStaffOrSuperuser} onLogout={handleLogout} />} />
            {/* Inventory Management */}
            <Route path="/inventory/inquiry" element={<InventoryInquiry />} />
            <Route path="/inventory/stock-movement-history" element={<StockMovementHistory />} />
            <Route path="/inventory/shipment" element={<ShipmentSchedule />} />
            <Route path="/inventory/purchase" element={<GoodsReceipt />} />
            <Route path="/inventory/issue" element={<GoodsIssue />} />
            {/* Production Management */}
            <Route path="/production/plan" element={<ProductionPlan />} />
            <Route path="/production/parts-used" element={<PartsUsed />} />
            <Route path="/production/material-allocation" element={<MaterialAllocation />} />
            <Route path="/production/work-progress" element={<WorkProgress />} />
            {/* Quality Management */}
            <Route path="/quality/process-inspection" element={<ProcessInspection />} />
            <Route path="/quality/acceptance-inspection" element={<AcceptanceInspection />} />
            <Route path="/quality/master-creation" element={<QualityMasterCreation />} />
            {/* Machine Management */}
            <Route path="/machine/start-inspection" element={<StartInspection />} />
            <Route path="/machine/inspection-history" element={<InspectionHistory />} />
            <Route path="/machine/master-creation" element={<MachineMasterCreation />} />
            {/* Data Maintenance & Account */}
            <Route path="/data/import" element={<DataImport />} />
            <Route path="/user/settings" element={<UserSettings />} />
            {isStaffOrSuperuser && <Route path="/user/management" element={<UserManagement />} />}
            {/* TODO: Add routes for other pages */}
          </Routes>
        </main>
      </div>
      <VersionModal isOpen={isVersionModalOpen} onClose={() => setVersionModalOpen(false)} />
    </Router>
  )
}

export default App
