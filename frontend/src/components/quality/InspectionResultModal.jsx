import React, { useState, useEffect, useCallback } from 'react';
import authFetch from '../../utils/api';
import './InspectionResultModal.css';

const InspectionResultModal = ({ item, onClose, onSuccess }) => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [baseFields, setBaseFields] = useState([]);
  const [measurementDetails, setMeasurementDetails] = useState([]);
  const [formData, setFormData] = useState({});
  const [submitting, setSubmitting] = useState(false);
  const [alert, setAlert] = useState({ show: false, type: '', message: '' });

  const fetchModalData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      // APIエンドポイントをViewSetのカスタムアクションのパスに修正
      const response = await authFetch(`/api/quality/inspection-items/${item.id}/form-data/`);
      if (!response.ok) {
        const errorText = await response.text(); // エラーレスポンスの本文を取得
        throw new Error(`HTTP error! status: ${response.status}, body: ${errorText}`);
      }
      const data = await response.json();
      if (!data.success) {
        throw new Error(data.message || 'フォームデータの取得に失敗しました。');
      }

      setBaseFields(data.result_form_fields);
      setMeasurementDetails(data.measurement_details);

      const initialFormData = {};
      data.result_form_fields.forEach(field => {
        initialFormData[field.name] = field.type === 'file' ? null : '';
      });
      data.measurement_details.forEach(detail => {
        initialFormData[`measurement_value_${detail.id}`] = '';
      });
      setFormData(initialFormData);

    } catch (e) {
      setError(e.message);
      console.error('Error fetching modal content:', e);
    } finally {
      setLoading(false);
    }
  }, [item.id]);

  useEffect(() => {
    fetchModalData();
    const handleEsc = (event) => {
      if (event.keyCode === 27) onClose();
    };
    window.addEventListener('keydown', handleEsc);
    return () => window.removeEventListener('keydown', handleEsc);
  }, [fetchModalData, onClose]);

  const handleInputChange = (e) => {
    const { name, value, type, files } = e.target;
    setFormData(prev => ({ ...prev, [name]: type === 'file' ? files[0] : value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    setAlert({ show: false, type: '', message: '' });

    const submissionData = new FormData();
    const measurementDetailsPayload = [];

    for (const key in formData) {
      if (key.startsWith('measurement_value_')) {
        const detailId = key.replace('measurement_value_', '');
        measurementDetailsPayload.push({
          measurement_detail_id: detailId,
          value: formData[key]
        });
      } else if (formData[key] !== null) {
        submissionData.append(key, formData[key]);
      }
    }

    submissionData.append('measurement_details_payload', JSON.stringify(measurementDetailsPayload));

    try {
      // APIエンドポイントをViewSetのカスタムアクションのパスに修正
      const response = await authFetch(`/api/quality/inspection-items/${item.id}/record-result/`, {
        method: 'POST',
        body: submissionData,
      });
      const result = await response.json();

      if (response.ok && result.success) {
        setAlert({ show: true, type: 'success', message: result.message || '検査結果を登録しました。' });
        setTimeout(() => {
          onSuccess();
          onClose();
        }, 2000);
      } else {
        let errorMessage = result.message || '登録に失敗しました。';
        if (result.errors) {
          errorMessage += ' 詳細: ' + Object.values(result.errors).flat().join('; ');
        }
        setAlert({ show: true, type: 'danger', message: errorMessage });
      }
    } catch (err) {
      console.error('Error submitting form:', err);
      setAlert({ show: true, type: 'danger', message: `送信エラーが発生しました: ${err.message}` });
    } finally {
      setSubmitting(false);
    }
  };

  const renderField = (field) => {
    const commonProps = { id: `id_${field.name}`, name: field.name, className: 'form-control form-control-sm', onChange: handleInputChange };
    let inputElement;
    if (field.type === 'select') {
      inputElement = <select {...commonProps} value={formData[field.name] || ''}><option value="">---------</option>{field.choices.map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select>;
    } else if (field.type === 'textarea') {
      inputElement = <textarea {...commonProps} rows="3" value={formData[field.name] || ''} />;
    } else if (field.type === 'file') {
      inputElement = <input type="file" {...commonProps} />;
    } else {
      inputElement = <input type={field.type} {...commonProps} value={formData[field.name] || ''} />;
    }
    return <div key={field.name} style={{ flex: '1 1 auto', minWidth: '200px' }} className="mb-3"><label htmlFor={`id_${field.name}`} className="form-label">{field.label}</label>{inputElement}</div>;
  };

  const renderMeasurementDetail = (detail) => {
    let specInfo = ` (タイプ: ${detail.measurement_type === 'quantitative' ? '定量' : '定性'}`;
    if (detail.measurement_type === 'quantitative') {
      if (detail.specification_nominal !== null) specInfo += `, 規格値: ${detail.specification_nominal}`;
      if (detail.specification_lower_limit !== null) specInfo += `, 下限: ${detail.specification_lower_limit}`;
      if (detail.specification_upper_limit !== null) specInfo += `, 上限: ${detail.specification_upper_limit}`;
      if (detail.specification_unit) specInfo += ` ${detail.specification_unit}`;
    } else if (detail.expected_qualitative_result) {
      specInfo += `, 期待結果: ${detail.expected_qualitative_result}`;
    }
    specInfo += `)`;
    return <div key={detail.id} className="col-12 mb-3 p-2 border rounded"><strong>{detail.name}</strong><small className="text-muted d-block">{specInfo}</small><input type={detail.measurement_type === 'quantitative' ? 'number' : 'text'} className="form-control form-control-sm mt-1" name={`measurement_value_${detail.id}`} value={formData[`measurement_value_${detail.id}`] || ''} onChange={handleInputChange} step={detail.measurement_type === 'quantitative' ? 'any' : undefined} /></div>;
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="custom-modal-content" onClick={e => e.stopPropagation()}>
        <form onSubmit={handleSubmit}>
          <div className="custom-modal-header">
            <h5 className="custom-modal-title">検査実施: {item.name}</h5>
            <button type="button" className="custom-modal-btn-close" aria-label="Close" onClick={onClose}>&times;</button>
          </div>
          <div className="custom-modal-body">
            {alert.show && <div className={`custom-alert custom-alert-${alert.type}`} role="alert">{alert.message}</div>}
            {loading && <p>ロード中...</p>}
            {error && <p className="text-danger">エラー: {error}</p>}
            {!loading && !error && (
              <>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '1rem' }}>{baseFields.map(renderField)}</div>
                <h5>測定・判定項目</h5>
                <div className="row">
                  {measurementDetails.length > 0 ? measurementDetails.map(renderMeasurementDetail) : <p className="text-muted">この検査項目に紐づく測定・判定項目はありません。</p>}
                </div>
              </>
            )}
          </div>
          <div className="custom-modal-footer">
            <button type="button" className="custom-btn custom-btn-secondary" onClick={onClose}>閉じる</button>
            <button type="submit" className="custom-btn custom-btn-primary" disabled={submitting || loading}>
              {submitting ? '登録中...' : '検査結果を登録'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default InspectionResultModal;