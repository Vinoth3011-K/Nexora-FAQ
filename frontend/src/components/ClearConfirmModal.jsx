import React from 'react';
import { AlertTriangle, X } from 'lucide-react';

export default function ClearConfirmModal({ isOpen, onClose, onConfirm, conversationTitle }) {
  if (!isOpen) return null;

  return (
    <div className="modal-overlay" role="dialog" aria-modal="true" aria-labelledby="clear-modal-title">
      <div className="modal-dialog">
        <div className="modal-header">
          <div className="modal-icon-badge" aria-hidden="true">
            <AlertTriangle className="modal-warning-icon" />
          </div>
          <h2 id="clear-modal-title" className="modal-title">Clear this conversation?</h2>
          <button 
            type="button" 
            className="modal-close-btn" 
            onClick={onClose}
            aria-label="Close dialog"
          >
            <X className="close-icon" />
          </button>
        </div>

        <div className="modal-body">
          <p className="modal-text">
            Are you sure you want to clear all messages in <strong>"{conversationTitle || 'Current Conversation'}"</strong>?
          </p>
          <p className="modal-subtext">
            This action will remove the conversation history from your browser session. Your other saved conversations will remain unaffected.
          </p>
        </div>

        <div className="modal-footer">
          <button 
            type="button" 
            className="modal-btn modal-btn-cancel" 
            onClick={onClose}
          >
            Cancel
          </button>
          <button 
            type="button" 
            className="modal-btn modal-btn-danger" 
            onClick={() => {
              onConfirm();
              onClose();
            }}
          >
            Clear Conversation
          </button>
        </div>
      </div>
    </div>
  );
}
