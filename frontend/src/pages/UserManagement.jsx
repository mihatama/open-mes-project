import React, { useState, useEffect, useCallback } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { getCookie } from '../utils/cookies';

const UserManagement = () => {
    const [users, setUsers] = useState([]);
    const [loading, setLoading] = useState(true);
    const [message, setMessage] = useState({ text: '', type: '' });
    const location = useLocation();
    const navigate = useNavigate();

    // Display messages passed via router state (e.g., after a redirect from create/edit)
    useEffect(() => {
        if (location.state?.message) {
            setMessage({ text: location.state.message, type: location.state.messageType || 'success' });
            // Clear the state to prevent message from re-appearing on refresh
            navigate(location.pathname, { replace: true, state: {} });
        }
    }, [location, navigate]);

    const fetchUsers = useCallback(async () => {
        setLoading(true);
        setMessage({ text: '', type: '' });
        try {
            // NOTE: This assumes a JSON-based API endpoint at /api/users/
            // This needs to be created in the Django backend.
            const response = await fetch('/api/users/');
            if (!response.ok) {
                const data = await response.json().catch(() => null);
                throw new Error(data?.detail || `HTTP error! status: ${response.status}`);
            }
            const data = await response.json();
            setUsers(data.results || data); // Support paginated or simple list response
        } catch (e) {
            setMessage({ text: `ユーザーデータの読み込みに失敗しました: ${e.message}`, type: 'danger' });
            console.error("Fetch error:", e);
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        fetchUsers();
    }, [fetchUsers]);

    const handleDelete = async (userId, userCustomId) => {
        if (window.confirm(`本当にユーザー "${userCustomId}" を削除しますか？この操作は元に戻せません。`)) {
            setMessage({ text: '', type: '' });
            const csrfToken = getCookie('csrftoken');
            try {
                // NOTE: This assumes a DELETE endpoint at /api/users/<id>/
                const response = await fetch(`/api/users/${userId}/`, {
                    method: 'DELETE',
                    headers: { 'X-CSRFToken': csrfToken },
                });

                if (response.ok) {
                    setMessage({ text: `ユーザー "${userCustomId}" を削除しました。`, type: 'success' });
                    fetchUsers(); // Refresh the user list
                } else {
                    const data = await response.json().catch(() => ({ detail: '削除に失敗しました。' }));
                    setMessage({ text: data.detail || '削除に失敗しました。', type: 'danger' });
                }
            } catch (err) {
                console.error('Delete request failed:', err);
                setMessage({ text: 'ユーザーの削除中にエラーが発生しました。', type: 'danger' });
            }
        }
    };

    const formatDate = (dateString) => {
        if (!dateString) return '-';
        // Format to 'YYYY-MM-DD HH:mm'
        return new Date(dateString).toISOString().slice(0, 16).replace('T', ' ');
    };

    return (
        <div>
            <h1>ユーザー管理</h1>

            {message.text && (
                <div className={`alert alert-${message.type} alert-dismissible fade show`} role="alert">
                    {message.text}
                    <button type="button" className="btn-close" data-bs-dismiss="alert" aria-label="Close" onClick={() => setMessage({ text: '', type: '' })}></button>
                </div>
            )}

            <div className="mb-3">
                <Link to="/admin/users/create" className="btn btn-primary">新規ユーザー作成</Link>
            </div>

            <table className="table table-striped table-hover">
                <thead>
                    <tr>
                        <th>専用ID</th>
                        <th>ユーザー名</th>
                        <th>メールアドレス</th>
                        <th className="text-center">スタッフ権限</th>
                        <th className="text-center">有効</th>
                        <th>登録日時</th>
                        <th>操作</th>
                    </tr>
                </thead>
                <tbody>
                    {loading ? (
                        <tr><td colSpan="7" className="text-center">読み込み中...</td></tr>
                    ) : users.length > 0 ? (
                        users.map(user => (
                            <tr key={user.id}>
                                <td>{user.custom_id}</td>
                                <td>{user.username || '-'}</td>
                                <td>{user.email || '-'}</td>
                                <td className="text-center">
                                    {user.is_staff ? <span className="badge bg-success">Yes</span> : <span className="badge bg-secondary">No</span>}
                                </td>
                                <td className="text-center">
                                    {user.is_active ? <span className="badge bg-success">Yes</span> : <span className="badge bg-danger">No</span>}
                                </td>
                                <td>{formatDate(user.date_joined)}</td>
                                <td>
                                    <Link to={`/admin/users/edit/${user.id}`} className="btn btn-sm btn-info">編集</Link>
                                    <button onClick={() => handleDelete(user.id, user.custom_id)} className="btn btn-sm btn-danger ms-1">削除</button>
                                </td>
                            </tr>
                        ))
                    ) : (
                        <tr><td colSpan="7" className="text-center">該当するユーザーがいません。</td></tr>
                    )}
                </tbody>
            </table>
        </div>
    );
};

export default UserManagement;