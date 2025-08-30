import { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import './LoginPage.css'; // Add some basic styling

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

    try {
      const response = await fetch('/api/users/token/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        // CustomUserのUSERNAME_FIELDである'custom_id'をキーとして送信
        body: JSON.stringify({ custom_id: customId, password }),
      });

      const data = await response.json();

      if (response.ok) {
        // トークンをlocalStorageに保存
        localStorage.setItem('access_token', data.access);
        localStorage.setItem('refresh_token', data.refresh);
        // Appコンポーネントにログイン成功を通知
        await onLoginSuccess();
      } else {
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