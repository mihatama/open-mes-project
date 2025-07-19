import React, { useState, useEffect } from 'react';
import InspectionResultModal from '../components/quality/InspectionResultModal';

const ProcessInspection = () => {
  const [inspectionItems, setInspectionItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedItem, setSelectedItem] = useState(null);

  useEffect(() => {
    const fetchInspectionItems = async () => {
      setLoading(true);
      setError(null);
      try {
        // APIエンドポイントを修正し、検査項目マスターのリストを取得
        const response = await fetch('/api/quality/inspection-items/');
        if (!response.ok) {
          const errorText = await response.text(); // エラーレスポンスの本文を取得
          throw new Error(`HTTP error! status: ${response.status}, body: ${errorText}`);
        }

        const data = await response.json();

        // APIのレスポンス形式に合わせてデータを処理し、工程内検査(in_process)で有効なもののみをフィルタリング
        if (data && data.status === 'success' && Array.isArray(data.data)) {
          const processInspectionItems = data.data.filter(item => item.inspection_type === 'in_process' && item.is_active);
          setInspectionItems(processInspectionItems);
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
  }, []); // Empty dependency array ensures this runs only once on mount

  const handleItemClick = (e, item) => {
    e.preventDefault();
    setSelectedItem(item);
  };

  const handleCloseModal = () => {
    setSelectedItem(null);
  };

  const handleSuccess = () => {
    setSelectedItem(null);
  };

  // Conditionally render the table only if there are items and no error
  const renderInspectionItemsTable = () => {
    if (inspectionItems.length === 0) {
      return <p className="text-muted">登録されている有効な検査項目がありません。</p>;
    }
    return (
      <table className="table table-hover">
        <thead>
          <tr>
            <th scope="col">コード</th>
            <th scope="col">名称</th>
            <th scope="col">検査タイプ</th>
            <th scope="col">対象</th>
          </tr>
        </thead>
        <tbody>
          {inspectionItems.map(item => (
            <tr key={item.id}>
              <td>{item.code}</td>
              <td>
                <a href="#" onClick={(e) => handleItemClick(e, item)} className="inspection-item-trigger">
                  {item.name}
                </a>
              </td>
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
      <h3>工程内検査 登録</h3>
      <p>検査する項目を選択してください。</p>

      {loading && <p>Loading...</p>}
      {error && <p className="text-danger">Error: {error}</p>}
      {!loading && !error && (
        <div id="inspectionItemsList">{renderInspectionItemsTable()}</div>
      )}

      {selectedItem && (
        <InspectionResultModal
          item={selectedItem}
          onClose={handleCloseModal}
          onSuccess={handleSuccess}
        />
      )}
    </div>
  );
};

export default ProcessInspection;