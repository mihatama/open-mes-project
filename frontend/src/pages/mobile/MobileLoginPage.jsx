import React, { useState } from 'react';
import { getCookie } from '../../utils/cookies.js';
import './MobileLoginPage.css';

const MobileLoginPage = ({ onLoginSuccess }) => {
    const [customId, setCustomId] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');

    const handleLogin = async (e) => {
        e.preventDefault();
        setError('');

        const csrfToken = getCookie('csrftoken');
        if (!csrfToken) {
            setError('CSRFトークンを取得できませんでした。ページをリロードしてください。');
            return;
        }

        try {
            const response = await fetch('/api/users/login/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken,
                },
                body: JSON.stringify({ custom_id: customId, password }),
                credentials: 'include',
            });

            if (response.ok) {
                await onLoginSuccess();
            } else {
                const data = await response.json().catch(() => null);
                let errorMessage = 'ログインに失敗しました。ユーザー名とパスワードを確認してください。'; // デフォルトメッセージ
                if (data) {
                    if (data.non_field_errors) {
                        errorMessage = data.non_field_errors.join(' ');
                    } else if (data.detail) {
                        errorMessage = data.detail;
                    } else if (typeof data === 'object' && !Array.isArray(data) && Object.keys(data).length > 0) {
                        const fieldErrors = Object.entries(data).map(([key, value]) => `${key}: ${Array.isArray(value) ? value.join(' ') : String(value)}`).join('; ');
                        if (fieldErrors) errorMessage = fieldErrors;
                    }
                }
                setError(errorMessage);
            }
        } catch (err) {
            console.error('ログインリクエスト失敗:', err);
            setError('ログイン中にエラーが発生しました。再度試してください。');
        }
    };

    return (
        <div className="mobile-login-container">
            <h2>ログイン</h2>
            {error && <p className="error-message">{error}</p>}

            <form onSubmit={handleLogin} className="mobile-login-form">
                <div className="form-group">
                    <label htmlFor="custom_id">ID:</label>
                    <input
                        type="text"
                        id="custom_id"
                        name="custom_id"
                        value={customId}
                        onChange={(e) => setCustomId(e.target.value)}
                        required
                    />
                </div>
                <div className="form-group">
                    <label htmlFor="password">パスワード:</label>
                    <input
                        type="password"
                        id="password"
                        name="password"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        required
                    />
                </div>
                <div className="form-group">
                    <button type="submit">ログイン</button>
                </div>
            </form>
        </div>
    );
};

export default MobileLoginPage;