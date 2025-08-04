import React, { useEffect, useRef } from 'react';
import { Html5QrcodeScanner } from 'html5-qrcode';
import './QrScannerModal.css';

const QrScannerModal = ({ show, onClose, onScanSuccess }) => {
    const scannerRef = useRef(null);

    useEffect(() => {
        if (show && !scannerRef.current) {
            const scanner = new Html5QrcodeScanner(
                'qr-reader',
                {
                    fps: 10,
                    qrbox: { width: 250, height: 250 },
                    rememberLastUsedCamera: true,
                },
                /* verbose= */ false
            );

            const successCallback = (decodedText, decodedResult) => {
                onScanSuccess(decodedText);
                scanner.clear().catch(error => console.error("Failed to clear scanner on success.", error));
                onClose();
            };

            const errorCallback = (error) => {
                // エラーはコンソールに表示しない（連続で発生するため）
            };

            scanner.render(successCallback, errorCallback);
            scannerRef.current = scanner;
        }

        return () => {
            if (scannerRef.current) {
                scannerRef.current.clear().catch(error => console.error("Failed to clear scanner on cleanup.", error));
                scannerRef.current = null;
            }
        };
    }, [show, onClose, onScanSuccess]);

    if (!show) return null;

    return (
        <div className="qr-scanner-modal-overlay">
            <div className="qr-scanner-modal-content">
                <div className="qr-scanner-header">
                    <h5>QRコードをスキャン</h5>
                    <button onClick={onClose} className="btn-close"></button>
                </div>
                <div id="qr-reader" style={{ width: '100%' }}></div>
            </div>
        </div>
    );
};

export default QrScannerModal;