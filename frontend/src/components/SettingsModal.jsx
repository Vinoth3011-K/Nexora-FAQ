import React from 'react';
import { Sliders, X, RotateCcw, Database } from 'lucide-react';
import { FAQS_DATA } from '../data/faqs.js';

export default function SettingsModal({
  isOpen,
  onClose,
  onResetAllData
}) {
  if (!isOpen) return null;

  return (
    <div className="modal-overlay" role="dialog" aria-modal="true" aria-labelledby="settings-modal-title">
      <div className="modal-dialog">
        <div className="modal-header">
          <div className="modal-icon-badge settings-badge" aria-hidden="true">
            <Sliders className="modal-icon" />
          </div>
          <h2 id="settings-modal-title" className="modal-title">System Settings & Status</h2>
          <button 
            type="button" 
            className="modal-close-btn" 
            onClick={onClose}
            aria-label="Close dialog"
          >
            <X className="close-icon" />
          </button>
        </div>

        <div className="modal-body settings-body">

          <div className="settings-section">
            <div className="settings-stat-card">
              <div className="stat-card-header">
                <Database className="stat-icon" aria-hidden="true" />
                <span className="stat-label">Knowledge Base Status</span>
              </div>
              <div className="stat-details">
                <span className="stat-value">{FAQS_DATA.length} Verified Entries</span>
                <span className="stat-sub">Across 5 Business Categories</span>
              </div>
            </div>
          </div>

          <div className="settings-section danger-boundary">
            <label className="settings-label">Reset Local Data</label>
            <p className="settings-hint">
              Clears all cached chat sessions from your browser storage.
            </p>
            <button
              type="button"
              className="settings-reset-btn"
              onClick={() => {
                if (window.confirm('Reset all saved conversations and local preferences?')) {
                  onResetAllData();
                  onClose();
                }
              }}
            >
              <RotateCcw className="btn-icon" aria-hidden="true" />
              Reset All Chat History
            </button>
          </div>
        </div>

        <div className="modal-footer">
          <button 
            type="button" 
            className="modal-btn modal-btn-cancel" 
            onClick={onClose}
          >
            Done
          </button>
        </div>
      </div>
    </div>
  );
}
