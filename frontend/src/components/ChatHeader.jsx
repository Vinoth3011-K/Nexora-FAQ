import React from 'react';
import { Bot, Menu, Trash2 } from 'lucide-react';

export default function ChatHeader({
  onToggleSidebar,
  onOpenClearModal,
  hasMessages = false,
  conversationTitle
}) {
  return (
    <header className="chat-header">
      <div className="header-left">
        <button
          type="button"
          className="sidebar-toggle-btn"
          onClick={onToggleSidebar}
          aria-label="Toggle navigation menu"
        >
          <Menu className="header-icon" />
        </button>

        <div className="header-bot-badge" aria-hidden="true">
          <Bot className="header-bot-icon" />
          <span className="status-indicator-dot" title="Assistant Online"></span>
        </div>

        <div className="header-titles">
          <div className="header-title-row">
            <h1 className="header-main-title">Company FAQ Assistant</h1>
          </div>
          <p className="header-subtitle">
            {conversationTitle ? `${conversationTitle} • Ask questions about our company` : 'Ask questions about our company'}
          </p>
        </div>
      </div>

      <div className="header-actions">
        <button
          type="button"
          className="header-action-btn clear-chat-btn"
          onClick={onOpenClearModal}
          disabled={!hasMessages}
          title={hasMessages ? 'Clear this conversation' : 'No messages to clear'}
          aria-label="Clear current conversation"
        >
          <Trash2 className="action-icon" />
          <span className="action-text">Clear Chat</span>
        </button>
      </div>
    </header>
  );
}
