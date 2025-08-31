import React, { useState, useEffect } from 'react';
import InspectionResultModal from '../components/quality/InspectionResultModal';
import authFetch from '../utils/api';

const AcceptanceInspection = () => {
  const [inspectionItems, setInspectionItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedItem, setSelectedItem] = useState(null);

  useEffect(() => {
    const fetchInspectionItems = async () => {
      setLoading(true);
      setError(null);
      try {
        // 検査項目マスターのリストを取得
        const response = await authFetch('/api/quality/inspection-items/');
        if (!response.ok) {
          const errorText = await response.text(); // エラーレスポンスの本文を取得
          throw new Error(`HTTP error! status: ${response.status}, body: ${errorText}`);
        }

        const data = await response.json();

        // APIのレスポンス形式に合わせてデータを処理し、受入検査(acceptance)で有効なもののみをフィルタリング
        if (data && data.status === 'success' && Array.isArray(data.data)) {
          const acceptanceInspectionItems = data.data.filter(item => item.inspection_type === 'acceptance' && item.is_active);
          setInspectionItems(acceptanceInspectionItems);
        } else {
          throw new Error(data.message || 'APIから無効なデータ形式が返されました。');
        }
      } catch (error) {
        console.error("Error fetching inspection items:", error);
        setError(error.message);
      } finally {
        setLoading(false);
      }
    };

    fetchInspectionItems();
  }, []); // 空の依存配列で、マウント時に一度だけ実行

  const handleItemClick = (e, item) => {
    e.preventDefault();
    setSelectedItem(item);
  };

  const handleCloseModal = () => {
    setSelectedItem(null);
  };

  const handleSuccess = () => {
    // 必要であれば、ここでリストを再読み込みするなどの処理を追加
    setSelectedItem(null);
  };

  const renderInspectionItemsTable = () => {
    if (inspectionItems.length === 0) {
      return <p className="text-muted">登録されている有効な受入検査項目がありません。</p>;
    }
    return (
      <table className="table table-hover">
        <thead><tr><th scope="col">コード</th><th scope="col">名称</th><th scope="col">検査タイプ</th><th scope="col">対象</th></tr></thead>
        <tbody>
          {inspectionItems.map(item => (
            <tr key={item.id}>
              <td>{item.code}</td>
              <td><a href="#" onClick={(e) => handleItemClick(e, item)}>{item.name}</a></td>
              <td>{item.inspection_type_display}</td>
              <td>{item.target_object_type_display}</td>
            </tr>
          ))}
        </tbody>
      </table>
    );
  };

  return (
    <div className="container mt-4">
      <h3>受入検査 登録</h3>
      <p>検査する項目を選択してください。</p>

      {loading && <p>Loading...</p>}
      {error && <p className="text-danger">Error: {error}</p>}
      {!loading && !error && <div>{renderInspectionItemsTable()}</div>}

      {selectedItem && (
        <InspectionResultModal item={selectedItem} onClose={handleCloseModal} onSuccess={handleSuccess} />
      )}
    </div>
  );
};

export default AcceptanceInspection;