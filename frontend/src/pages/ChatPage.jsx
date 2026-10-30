import React, { useRef, useEffect, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import ChatHeader from '../components/ChatHeader';
import WelcomeScreen from '../components/WelcomeScreen';
import ChatMessage from '../components/ChatMessage';
import ChatInput from '../components/ChatInput';
import LoadingIndicator from '../components/LoadingIndicator';
import ClearConfirmModal from '../components/ClearConfirmModal';

const processedActionKeys = new Set();

export default function ChatPage({
  activeConversation,
  isLoading,
  onSendMessage,
  onClearConversation,
  onToggleSidebar,
}) {
  const location = useLocation();
  const navigate = useNavigate();
  const [isClearModalOpen, setIsClearModalOpen] = useState(false);
  const messagesEndRef = useRef(null);
  const messageAreaRef = useRef(null);
  const lastProcessedKeyRef = useRef(null);

  useEffect(() => {
    const askQuestion = location.state?.askQuestion;
    const askTimestamp = location.state?.timestamp;

    if (askQuestion && askTimestamp) {
      if (lastProcessedKeyRef.current === askTimestamp || processedActionKeys.has(askTimestamp)) {
        return;
      }
      lastProcessedKeyRef.current = askTimestamp;
      processedActionKeys.add(askTimestamp);

      navigate(location.pathname, { replace: true, state: {} });
      onSendMessage(askQuestion);
    }
  }, [location.state, location.pathname, navigate, onSendMessage]);

  const messages = activeConversation?.messages || [];
  const hasMessages = messages.length > 0;
  const returnScrollTop = location.state?.returnScrollTop;

  useEffect(() => {
    if (typeof returnScrollTop === 'number' && messageAreaRef.current) {
      const scrollContainer = messageAreaRef.current.querySelector('.messages-scroll-container') || messageAreaRef.current;
      scrollContainer.scrollTop = returnScrollTop;
      navigate(location.pathname, { replace: true, state: {} });
    } else if (messagesEndRef.current && typeof returnScrollTop !== 'number') {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, isLoading, returnScrollTop, location.pathname, navigate]);

  return (
    <div className="chat-page-container">
      <ChatHeader
        onToggleSidebar={onToggleSidebar}
        onOpenClearModal={() => setIsClearModalOpen(true)}
        hasMessages={hasMessages}
        conversationTitle={activeConversation?.title || ''}
      />

      <main className="chat-main-area" ref={messageAreaRef}>
        {!hasMessages && !isLoading ? (
          <WelcomeScreen onSelectQuestion={onSendMessage} disabled={isLoading} />
        ) : (
          <div className="messages-scroll-container" role="log" aria-live="polite">
            <div className="messages-inner-wrapper">
              {messages.map((msg) => (
                <ChatMessage
                  key={msg.id}
                  message={msg}
                  activeConversationId={activeConversation?.id}
                  onRetry={onSendMessage}
                />
              ))}

              {isLoading && <LoadingIndicator />}
              <div ref={messagesEndRef} className="scroll-anchor" />
            </div>
          </div>
        )}
      </main>

      <footer className="chat-footer-dock">
        <ChatInput
          onSendMessage={onSendMessage}
          disabled={isLoading}
          placeholder="Ask a question about our company..."
        />
      </footer>

      <ClearConfirmModal
        isOpen={isClearModalOpen}
        onClose={() => setIsClearModalOpen(false)}
        onConfirm={onClearConversation}
        conversationTitle={activeConversation?.title || 'Current Chat'}
      />
    </div>
  );
}
