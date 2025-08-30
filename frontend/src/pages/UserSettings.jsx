import React, { useState, useEffect, useCallback } from 'react';
import authFetch from '../utils/api';
import Modal from '../components/Modal';

const UserSettings = () => {
  // State for forms, data, and UI
  const [profileForm, setProfileForm] = useState({
    username: '',
    email: '',
    custom_id: '',
  });
  const [passwordForm, setPasswordForm] = useState({
    old_password: '',
    new_password1: '',
    new_password2: '',
  });
  const [apiToken, setApiToken] = useState(null);
  const [isTokenVisible, setIsTokenVisible] = useState(false);

  // State for UI feedback
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(''); // General error for page load
  const [messages, setMessages] = useState([]); // For success/error banners
  const [profileErrors, setProfileErrors] = useState({});
  const [passwordErrors, setPasswordErrors] = useState({});

  // State for password modal
  const [isPasswordModalOpen, setIsPasswordModalOpen] = useState(false);

  // Helper to add messages
  const addMessage = (text, type = 'info') => {
    const id = new Date().getTime();
    setMessages(prev => [...prev, { id, text, type }]);
    setTimeout(() => {
      setMessages(prev => prev.filter(msg => msg.id !== id));
    }, 5000);
  };

  // Fetch initial data
  const fetchUserData = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const [profileRes, tokenRes] = await Promise.all([authFetch('/api/users/settings/'), authFetch('/api/users/settings/token/')]);

      if (!profileRes.ok) {
        const errorData = await profileRes.json().catch(() => ({ detail: 'ユーザーデータの読み込みに失敗しました。' }));
        throw new Error(errorData.detail || 'ユーザーデータの読み込みに失敗しました。');
      }
      const profileData = await profileRes.json();
      setProfileForm({
        username: profileData.username || '',
        email: profileData.email || '',
        custom_id: profileData.custom_id || '',
      });

      if (tokenRes.ok) {
        const tokenData = await tokenRes.json();
        setApiToken(tokenData.api_token || null);
      } else {
        console.warn("APIトークンの取得に失敗しました。");
        setApiToken(null);
      }
    } catch (e) {
      setError(e.message);
      console.error("Fetch user data error:", e);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchUserData();
  }, [fetchUserData]);

  // Form change handlers
  const handleProfileChange = (e) => {
    const { name, value } = e.target;
    setProfileForm(prev => ({ ...prev, [name]: value }));
  };

  const handlePasswordChange = (e) => {
    const { name, value } = e.target;
    setPasswordForm(prev => ({ ...prev, [name]: value }));
  };

  // Form submission handlers
  const handleProfileSubmit = async (e) => {
    e.preventDefault();
    setProfileErrors({});
    try {
      const response = await authFetch('/api/users/settings/', {
        method: 'PATCH',
        body: JSON.stringify({
          username: profileForm.username,
          email: profileForm.email,
        }),
      });
      const data = await response.json();
      if (!response.ok) {
        if (response.status === 400) {
          setProfileErrors(data);
        }
        throw new Error(data.detail || data.error || 'プロフィールの更新に失敗しました。');
      }
      addMessage(data.message || 'プロフィール情報が更新されました。', 'success');
    } catch (err) {
      addMessage(err.message, 'danger');
    }
  };

  const handlePasswordSubmit = async (e) => {
    e.preventDefault();
    setPasswordErrors({});
    try {
      const response = await authFetch('/api/users/settings/password/', {
        method: 'POST',
        body: JSON.stringify(passwordForm),
      });
      const data = await response.json();
      if (!response.ok) {
        if (response.status === 400) {
          setPasswordErrors(data);
        }
        throw new Error(data.detail || data.error || 'パスワードの変更に失敗しました。');
      }
      addMessage(data.message || 'パスワードが正常に変更されました。', 'success');
      closePasswordModal();
    } catch (err) {
      // Non-field errors are often in 'detail' or a top-level error key
      setPasswordErrors(prev => ({ ...prev, non_field_errors: [err.message] }));
    }
  };

  const handleRegenerateToken = async () => {
    if (!window.confirm('トークンを再生成しますか？現在のトークンは無効になります。')) {
      return;
    }
    try {
      const response = await authFetch('/api/users/settings/token/', { method: 'POST' });
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.error || data.detail || 'トークンの再生成に失敗しました。');
      }
      setApiToken(data.api_token);
      addMessage(data.message || 'APIトークンが再生成されました。', 'success');
      setIsTokenVisible(true); // Show the new token immediately
    } catch (err) {
      addMessage(err.message, 'danger');
    }
  };

  // Modal controls
  const openPasswordModal = () => {
    setPasswordForm({ old_password: '', new_password1: '', new_password2: '' });
    setPasswordErrors({});
    setIsPasswordModalOpen(true);
  };

  const closePasswordModal = () => setIsPasswordModalOpen(false);

  // Render logic
  if (loading) {
    return <div className="container mt-4"><h2>ユーザー設定</h2><p>読み込み中...</p></div>;
  }

  if (error) {
    return <div className="container mt-4"><h2>ユーザー設定</h2><div className="alert alert-danger">{error}</div></div>;
  }

  const renderMessages = () => {
    return messages.map(msg => (
      <div key={msg.id} className={`alert alert-${msg.type} alert-dismissible fade show`} role="alert">
        {msg.text}
        <button type="button" className="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
      </div>
    ));
  };

  return (
    <div className="container mt-4">
      <h2>ユーザー設定</h2>
      {renderMessages()}

      {/* Profile Edit Form */}
      <div className="card mb-4">
        <div className="card-header">
          <h3>プロフィール編集</h3>
        </div>
        <div className="card-body">
          <form onSubmit={handleProfileSubmit}>
            {profileErrors.non_field_errors && <div className="alert alert-danger">{profileErrors.non_field_errors.join(' ')}</div>}
            <div className="row mb-3">
              <label htmlFor="custom_id" className="col-sm-3 col-form-label fw-bold">専用ID</label>
              <div className="col-sm-9">
                <input type="text" id="custom_id" name="custom_id" className="form-control" value={profileForm.custom_id} readOnly disabled />
                {profileErrors.custom_id && <div className="invalid-feedback">{profileErrors.custom_id.join(' ')}</div>}
              </div>
            </div>
            <div className="row mb-3">
              <label htmlFor="username" className="col-sm-3 col-form-label fw-bold">ユーザー名</label>
              <div className="col-sm-9">
                <input type="text" id="username" name="username" className={`form-control ${profileErrors.username ? 'is-invalid' : ''}`} value={profileForm.username} onChange={handleProfileChange} required />
                {profileErrors.username && <div className="invalid-feedback">{profileErrors.username.join(' ')}</div>}
              </div>
            </div>
            <div className="row mb-3">
              <label htmlFor="email" className="col-sm-3 col-form-label fw-bold">メールアドレス</label>
              <div className="col-sm-9">
                <input type="email" id="email" name="email" className={`form-control ${profileErrors.email ? 'is-invalid' : ''}`} value={profileForm.email} onChange={handleProfileChange} />
                {profileErrors.email && <div className="invalid-feedback">{profileErrors.email.join(' ')}</div>}
              </div>
            </div>
            <div className="row mt-4">
              <div className="col-sm-9 offset-sm-3">
                <button type="submit" className="btn btn-primary">プロフィール情報を保存</button>
              </div>
            </div>
          </form>
        </div>
      </div>

      {/* Password Change */}
      <div className="card mb-4">
        <div className="card-header">
          <h3>パスワード変更</h3>
        </div>
        <div className="card-body">
          <button type="button" className="btn btn-secondary" onClick={openPasswordModal}>
            パスワードを変更する
          </button>
        </div>
      </div>

      {/* API Token Management */}
      <div className="card">
        <div className="card-header">
          <h3>APIトークン</h3>
        </div>
        <div className="card-body">
          <p><strong>現在のトークン:</strong>
            <span id="apiTokenDisplay" style={{ wordBreak: 'break-all' }} className="ms-2 font-monospace">
              {apiToken ? (isTokenVisible ? apiToken : '•'.repeat(40)) : 'トークンが見つかりません。'}
            </span>
            <button
              id="toggleTokenVisibility"
              className="btn btn-sm btn-outline-secondary ms-2"
              onClick={() => setIsTokenVisible(!isTokenVisible)}
              disabled={!apiToken}
            >
              {isTokenVisible ? '非表示' : '表示する'}
            </button>
          </p>
          <form onSubmit={(e) => { e.preventDefault(); handleRegenerateToken(); }} className="mt-2">
            <button type="submit" name="regenerate_token" className="btn btn-warning">トークンを再生成</button>
          </form>
          <p className="mt-2"><small>トークンを再生成すると、現在のトークンは無効になり、新しいトークンが作成されます。</small></p>
        </div>
      </div>

      {/* Password Change Modal */}
      <Modal isOpen={isPasswordModalOpen} onClose={closePasswordModal}>
        <form onSubmit={handlePasswordSubmit} noValidate>
          <div className="modal-header">
            <h5 className="modal-title">パスワード変更</h5>
            <button type="button" className="btn-close" onClick={closePasswordModal}></button>
          </div>
          <div className="modal-body">
            {passwordErrors.non_field_errors && <div className="alert alert-danger">{passwordErrors.non_field_errors.join(' ')}</div>}
            <div className="mb-3">
              <label htmlFor="old_password" className="form-label">現在のパスワード</label>
              <input type="password" id="old_password" name="old_password" className={`form-control ${passwordErrors.old_password ? 'is-invalid' : ''}`} value={passwordForm.old_password} onChange={handlePasswordChange} required />
              {passwordErrors.old_password && <div className="invalid-feedback">{passwordErrors.old_password.join(' ')}</div>}
            </div>
            <div className="mb-3">
              <label htmlFor="new_password1" className="form-label">新しいパスワード</label>
              <input type="password" id="new_password1" name="new_password1" className={`form-control ${passwordErrors.new_password1 ? 'is-invalid' : ''}`} value={passwordForm.new_password1} onChange={handlePasswordChange} required />
              {passwordErrors.new_password1 && <div className="invalid-feedback">{passwordErrors.new_password1.join(' ')}</div>}
            </div>
            <div className="mb-3">
              <label htmlFor="new_password2" className="form-label">新しいパスワード（確認）</label>
              <input type="password" id="new_password2" name="new_password2" className={`form-control ${passwordErrors.new_password2 ? 'is-invalid' : ''}`} value={passwordForm.new_password2} onChange={handlePasswordChange} required />
              {passwordErrors.new_password2 && <div className="invalid-feedback">{passwordErrors.new_password2.join(' ')}</div>}
            </div>
          </div>
          <div className="modal-footer">
            <button type="button" className="btn btn-secondary" onClick={closePasswordModal}>キャンセル</button>
            <button type="submit" className="btn btn-primary">パスワードを保存</button>
          </div>
        </form>
      </Modal>
    </div>
  );
};

export default UserSettings;