import { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import './LoginPage.css'; // Add some basic styling
import { getCookie } from '../utils/cookies.js';

const LoginPage = ({ onLoginSuccess }) => {
  const [customId, setCustomId] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const navigate = useNavigate();
  const location = useLocation();

  const from = location.state?.from?.pathname || "/";

  const handleLogin = async (e) => {
    e.preventDefault();
    setError('');

    const csrfToken = getCookie('csrftoken');
    if (!csrfToken) {
      setError('Could not get CSRF token. Please refresh the page.');
      return;
    }

    try {
      // NOTE: This assumes a JSON-based API endpoint at /api/users/login/
      // This may need to be created in the Django backend.
      const response = await fetch('/api/users/login/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': csrfToken,
        },
        body: JSON.stringify({ custom_id: customId, password }),
        credentials: 'include', // クロスオリジンリクエストでクッキーを送信するために必要
      });

      if (response.ok) {
        // ログイン成功後、親コンポーネント(App.jsx)が状態を更新し、
        // 自動的にリダイレクト処理を行うため、ここでのnavigateは不要です。
        await onLoginSuccess();
      } else {
        // Parse error message from backend for more detailed feedback
        const data = await response.json().catch(() => null);
        let errorMessage = 'Login failed. Please check your credentials and try again.'; // Default message
        if (data) {
            if (data.non_field_errors) {
                errorMessage = data.non_field_errors.join(' ');
            } else if (data.detail) {
                errorMessage = data.detail;
            } else if (typeof data === 'object' && !Array.isArray(data) && Object.keys(data).length > 0) {
                // Handle field-specific errors (e.g., {'password': ['This field is required.']})
                const fieldErrors = Object.entries(data).map(([key, value]) => `${key}: ${Array.isArray(value) ? value.join(' ') : String(value)}`).join('; ');
                if (fieldErrors) errorMessage = fieldErrors;
            }
        }
        setError(errorMessage);
      }
    } catch (err) {
      console.error('Login request failed:', err);
      setError('An error occurred during login. Please try again later.');
    }
  };

  return (
    <div className="login-page-container">
      <div className="login-card">
        <h2 className="login-title">みんなのMES</h2>
        {error && <div className="alert alert-danger">{error}</div>}
        <form onSubmit={handleLogin} className="login-form">
          <div className="form-group">
            <input
              type="text"
              id="custom_id"
              className="form-control"
              placeholder="ID"
              value={customId}
              onChange={(e) => setCustomId(e.target.value)}
              required
              autoFocus
            />
          </div>
          <div className="form-group">
            <input
              type="password"
              id="password"
              className="form-control"
              placeholder="パスワード"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>
          <div className="form-group">
            <button
              type="submit"
              className="btn btn-primary btn-block"
              style={{ backgroundColor: '#007bff', borderColor: '#007bff' }}
            >
              ログイン
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default LoginPage;