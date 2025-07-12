import { useState, useEffect } from 'react';
import './App.css';
import Header from './components/Header';
import SideMenu from './components/SideMenu';
import VersionModal from './components/VersionModal';

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
    <>
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
          <div className="top-page-container">
            <div className="menu-section">
              <h3>在庫管理</h3>
              <ul>
                <li><a href="#">在庫照会</a></li>
                <li><a href="#">入出庫履歴</a></li>
                <li><a href="#">出庫予定</a></li>
                <li><a href="#">入庫処置</a></li>
                <li><a href="#">出庫処理</a></li>
              </ul>
            </div>

            <div className="menu-section">
              <h3>生産管理</h3>
              <ul>
                <li><a href="#">生産計画</a></li>
                <li><a href="#">使用部品</a></li>
                <li><a href="#">材料引当</a></li>
                <li><a href="#">作業進捗</a></li>
              </ul>
            </div>

            <div className="menu-section">
              <h3>品質管理</h3>
              <ul>
                <li><a href="#">工程内検査</a></li>
                <li><a href="#">受入検査</a></li>
                <li><a href="#">マスター作成</a></li>
              </ul>
            </div>

            <div className="menu-section">
              <h3>設備管理</h3>
              <ul>
                <li><a href="#">始業点検</a></li>
                <li><a href="#">点検履歴</a></li>
                <li><a href="#">マスター作成</a></li>
              </ul>
            </div>

            <div className="menu-section">
              <h3>データメンテナンス</h3>
              <ul>
                <li><a href="#">データ投入</a></li>
              </ul>
            </div>

            <div className="menu-section">
              <h3>アカウント</h3>
              <ul>
                {isAuthenticated ? (
                  <>
                    <li><a href="#">ユーザー設定</a></li>
                    {isStaffOrSuperuser && (
                      <li><a href="#">ユーザー管理</a></li>
                    )}
                    <li>
                      <form id="logout-form-top" action="#" method="post" style={{ display: 'inline' }}>
                        <button type="submit" className="link-button">ログアウト</button>
                      </form>
                    </li>
                  </>
                ) : (
                  <li><a href="#">ログイン</a></li>
                )}
              </ul>
            </div>
          </div>
        </main>
      </div>
      <VersionModal isOpen={isVersionModalOpen} onClose={() => setVersionModalOpen(false)} />
    </>
  )
}

export default App
