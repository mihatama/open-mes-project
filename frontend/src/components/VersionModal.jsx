import React from 'react';
import Modal from './Modal';

const VersionModal = ({ isOpen, onClose }) => {
  // TODO: Fetch version from backend API
  const version = '0.0.0';
  const credit = '© Open MES Project. since 2025';
  
  return (
    <Modal isOpen={isOpen} onClose={onClose}>
      <div className="version-modal-content">
        <h2>バージョン情報</h2>
        <p><strong>みんなのMES</strong></p>
        <p>Version: {version}</p>
        <hr />
        <p className="credit">{credit}</p>
      </div>
    </Modal>
  );
};

export default VersionModal;