import React from 'react';
import { Bot } from 'lucide-react';

export default function LoadingIndicator() {
  return (
    <div className="chat-message assistant-message loading-state" role="status" aria-live="polite">
      <div className="message-avatar assistant-avatar" aria-hidden="true">
        <Bot className="avatar-icon" />
      </div>
      <div className="message-content">
        <div className="message-header-meta">
          <span className="sender-name">Nexora Assistant</span>
          <span className="badge-searching">Searching knowledge base...</span>
        </div>
        <div className="typing-bubble">
          <span className="typing-dot"></span>
          <span className="typing-dot"></span>
          <span className="typing-dot"></span>
        </div>
      </div>
    </div>
  );
}
