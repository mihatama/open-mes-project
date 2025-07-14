import { useState, useEffect, useCallback } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, useNavigate, useLocation } from 'react-router-dom';
import './App.css';
import { getCookie } from './utils/cookies.js';
import Header from './components/Header.jsx';
import SideMenu from './components/SideMenu.jsx';
import ProtectedRoute from './components/ProtectedRoute.jsx';
import LoginPage from './pages/LoginPage.jsx';
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
import MobileTopPage from './pages/MobileTopPage.jsx';

// モバイルデバイスからのアクセス時にリダイレクトを行うためのコンポーネント
const MobileRedirector = () => {
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
    const isMobilePage = location.pathname === '/mobile';
    const isLoginPage = location.pathname === '/login';

    // モバイルデバイスで、かつモバイルページでもログインページでもない場合にリダイレクト
    if (isMobile && !isMobilePage && !isLoginPage) {
      navigate('/mobile', { replace: true });
    }
  }, [location.pathname, navigate]);

  return null; // このコンポーネントはUIを描画しません
};

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isStaffOrSuperuser, setIsStaffOrSuperuser] = useState(false);
  const [isMenuOpen, setMenuOpen] = useState(false);
  const [isVersionModalOpen, setVersionModalOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(true); // ローディング状態を追加

  const checkAuthStatus = useCallback(async () => {
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
  }, []); // stateのセッター関数は依存配列に含める必要はありません

  useEffect(() => {
    // アプリケーションのロード時にセッション情報を確認
    checkAuthStatus();
  }, [checkAuthStatus]); // コンポーネントのマウント時に一度だけ実行

  const handleLoginSuccess = async () => {
    // ログイン成功後に認証状態を再チェック
    await checkAuthStatus();
  };

  const handleLogout = async () => {
    const csrfToken = getCookie('csrftoken');
    await fetch('/api/users/logout/', {
      method: 'POST',
      headers: {
        'X-CSRFToken': csrfToken,
      },
    });
    // 状態を更新して、UI側でリダイレクトをハンドリングさせる
    setIsAuthenticated(false);
    setIsStaffOrSuperuser(false);
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
      {/* 認証済みの場合、モバイルリダイレクト機能を有効化 */}
      {isAuthenticated && <MobileRedirector />}

      {isAuthenticated && (
        <Header onMenuClick={toggleMenu} isMenuOpen={isMenuOpen} isAuthenticated={isAuthenticated} />
      )}
      {isAuthenticated && (
        <SideMenu
          isOpen={isMenuOpen}
          isStaffOrSuperuser={isStaffOrSuperuser}
          onVersionClick={() => setVersionModalOpen(true)}
          onLinkClick={closeMenu}
          onLogout={handleLogout}
        />
      )}
      {isAuthenticated && isMenuOpen && <div id="menu-overlay" onClick={toggleMenu}></div>}
      <main className={isAuthenticated ? "main-contents container" : ""}>
        <Routes>
          <Route path="/login" element={isAuthenticated ? <Navigate to="/" /> : <LoginPage onLoginSuccess={handleLoginSuccess} />} />

          {/* Protected Routes */}
          <Route path="/" element={<ProtectedRoute isAuthenticated={isAuthenticated}><TopPage isStaffOrSuperuser={isStaffOrSuperuser} isAuthenticated={isAuthenticated} onLogout={handleLogout} /></ProtectedRoute>} />
          <Route path="/mobile" element={<ProtectedRoute isAuthenticated={isAuthenticated}><MobileTopPage /></ProtectedRoute>} />
          {/* Inventory Management */}
          <Route path="/inventory/inquiry" element={<ProtectedRoute isAuthenticated={isAuthenticated}><InventoryInquiry /></ProtectedRoute>} />
          <Route path="/inventory/stock-movement-history" element={<ProtectedRoute isAuthenticated={isAuthenticated}><StockMovementHistory /></ProtectedRoute>} />
          <Route path="/inventory/shipment" element={<ProtectedRoute isAuthenticated={isAuthenticated}><ShipmentSchedule /></ProtectedRoute>} />
          <Route path="/inventory/purchase" element={<ProtectedRoute isAuthenticated={isAuthenticated}><GoodsReceipt /></ProtectedRoute>} />
          <Route path="/inventory/issue" element={<ProtectedRoute isAuthenticated={isAuthenticated}><GoodsIssue /></ProtectedRoute>} />
          {/* Production Management */}
          <Route path="/production/plan" element={<ProtectedRoute isAuthenticated={isAuthenticated}><ProductionPlan /></ProtectedRoute>} />
          <Route path="/production/parts-used" element={<ProtectedRoute isAuthenticated={isAuthenticated}><PartsUsed /></ProtectedRoute>} />
          <Route path="/production/material-allocation" element={<ProtectedRoute isAuthenticated={isAuthenticated}><MaterialAllocation /></ProtectedRoute>} />
          <Route path="/production/work-progress" element={<ProtectedRoute isAuthenticated={isAuthenticated}><WorkProgress /></ProtectedRoute>} />
          {/* Quality Management */}
          <Route path="/quality/process-inspection" element={<ProtectedRoute isAuthenticated={isAuthenticated}><ProcessInspection /></ProtectedRoute>} />
          <Route path="/quality/acceptance-inspection" element={<ProtectedRoute isAuthenticated={isAuthenticated}><AcceptanceInspection /></ProtectedRoute>} />
          <Route path="/quality/master-creation" element={<ProtectedRoute isAuthenticated={isAuthenticated}><QualityMasterCreation /></ProtectedRoute>} />
          {/* Machine Management */}
          <Route path="/machine/start-inspection" element={<ProtectedRoute isAuthenticated={isAuthenticated}><StartInspection /></ProtectedRoute>} />
          <Route path="/machine/inspection-history" element={<ProtectedRoute isAuthenticated={isAuthenticated}><InspectionHistory /></ProtectedRoute>} />
          <Route path="/machine/master-creation" element={<ProtectedRoute isAuthenticated={isAuthenticated}><MachineMasterCreation /></ProtectedRoute>} />
          {/* Data Maintenance & Account */}
          <Route path="/data/import" element={<ProtectedRoute isAuthenticated={isAuthenticated}><DataImport /></ProtectedRoute>} />
          <Route path="/user/settings" element={<ProtectedRoute isAuthenticated={isAuthenticated}><UserSettings /></ProtectedRoute>} />
          <Route
            path="/user/management"
            element={<ProtectedRoute isAuthenticated={isAuthenticated && isStaffOrSuperuser}><UserManagement /></ProtectedRoute>}
          />
          {/* Redirect any other path to top page if authenticated, or login if not */}
          <Route path="*" element={<Navigate to="/" />} />
        </Routes>
      </main>
      <VersionModal isOpen={isVersionModalOpen} onClose={() => setVersionModalOpen(false)} />
    </Router>
  )
}

export default App
