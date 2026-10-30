import React, { useState, useRef, useEffect } from 'react';
import { SendHorizonal } from 'lucide-react';

export default function ChatInput({ onSendMessage, disabled = false, placeholder = 'Ask a question about our company...' }) {
  const [inputText, setInputText] = useState('');
  const textareaRef = useRef(null);

  // Auto-adjust height based on content
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      const scrollHeight = textareaRef.current.scrollHeight;
      // Cap at reasonable max height ~160px
      textareaRef.current.style.height = `${Math.min(scrollHeight, 160)}px`;
    }
  }, [inputText]);

  const handleSubmit = (e) => {
    if (e) e.preventDefault();
    const trimmed = inputText.trim();
    if (!trimmed || disabled) return;
    onSendMessage(trimmed);
    setInputText('');
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const isSendDisabled = disabled || !inputText.trim();

  return (
    <div className="chat-input-container">
      <form onSubmit={handleSubmit} className="chat-input-form" role="search" aria-label="Ask chatbot">
        <div className="chat-input-wrapper">
          <label htmlFor="chat-textarea" className="visually-hidden">
            Ask a question
          </label>
          <textarea
            id="chat-textarea"
            ref={textareaRef}
            rows={1}
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={placeholder}
            disabled={disabled}
            className="chat-textarea"
            aria-label="Ask a question about our company"
          />

          <button
            type="submit"
            className="chat-send-btn"
            disabled={isSendDisabled}
            aria-label="Send message"
            title="Send (Enter)"
          >
            <SendHorizonal className="send-icon" />
          </button>
        </div>
      </form>
    </div>
  );
}
