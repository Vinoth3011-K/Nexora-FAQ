import React, { useState, useEffect, useCallback, useRef } from 'react';
import { Routes, Route, useNavigate, useLocation } from 'react-router-dom';
import AuthGate from './components/AuthGate';
import { useAuth } from './context/AuthContext';
import Sidebar from './components/Sidebar';
import SettingsModal from './components/SettingsModal';
import ChatPage from './pages/ChatPage';
import FAQPage from './pages/FAQPage';
import SourceDetailPage from './pages/SourceDetailPage';
import AboutPage from './pages/AboutPage';
import {
  getStoredConversations,
  saveStoredConversations,
  getStoredActiveId,
  saveStoredActiveId,
  createNewConversation,
} from './utils/storage';
import {
  sendChatMessage,
  fetchConversations,
  fetchConversation,
  clearConversation,
  getAuthToken,
} from './services/api';

function ChatApplication() {
  const navigate = useNavigate();
  const location = useLocation();
  const { isAuthenticated, isLoading: authLoading } = useAuth();

  const historyLoadedRef = useRef(false);

  const [conversations, setConversations] = useState(() => {
    const saved = getStoredConversations();
    if (saved?.length) {
      const nonEmpty = saved.filter((c) => c.messages && c.messages.length > 0);
      const firstEmpty = saved.find((c) => !c.messages || c.messages.length === 0);
      const cleaned = firstEmpty ? [firstEmpty, ...nonEmpty] : nonEmpty;
      if (cleaned.length) return cleaned;
    }
    return [createNewConversation('New Conversation')];
  });

  const [activeConversationId, setActiveConversationId] = useState(() => {
    return getStoredActiveId() || conversations[0]?.id || null;
  });

  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);

  // Sync to local storage
  useEffect(() => {
    if (activeConversationId) {
      saveStoredActiveId(activeConversationId);
    }
  }, [activeConversationId]);

  useEffect(() => {
    saveStoredConversations(conversations);
  }, [conversations]);

  // Restore conversation if navigated back from a source detail page
  useEffect(() => {
    const returnId = location.state?.returnToConversationId || location.state?.targetConversationId;
    if (returnId && returnId !== activeConversationId) {
      setActiveConversationId(returnId);
    }
  }, [location.state]);

  // Reset conversation state on logout
  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      const fresh = createNewConversation('New Conversation');
      setConversations([fresh]);
      setActiveConversationId(fresh.id);
      historyLoadedRef.current = false;
    }
  }, [isAuthenticated, authLoading]);

  // Fetch conversation history from the server once authenticated
  useEffect(() => {
    if (authLoading || !isAuthenticated || historyLoadedRef.current) return;
    if (!getAuthToken()) return;

    let isMounted = true;
    historyLoadedRef.current = true;

    async function loadServerHistory() {
      try {
        const serverConvs = await fetchConversations();
        if (!isMounted || !Array.isArray(serverConvs) || serverConvs.length === 0) return;

        const normalized = serverConvs
          .map((sc) => ({
            id: String(sc.id),
            title: sc.title || 'New Conversation',
            messages: Array.isArray(sc.messages) ? sc.messages : [],
            createdAt: sc.createdAt || sc.created_at || new Date().toISOString(),
            updatedAt: sc.updatedAt || sc.updated_at || new Date().toISOString(),
          }))
          .filter((sc) => sc.messages.length > 0);

        if (!normalized.length) return;

        setConversations((prev) => {
          const activeDraft = prev.find(
            (c) => c.id === activeConversationId && (!c.messages || c.messages.length === 0) && String(c.id).startsWith('conv_')
          );
          return activeDraft ? [activeDraft, ...normalized.filter((c) => c.id !== activeDraft.id)] : normalized;
        });

        setActiveConversationId((currentId) => {
          const savedId = getStoredActiveId();
          const target = currentId || savedId;
          const exists = normalized.some((c) => String(c.id) === String(target));
          if (exists) return target;
          if (target && String(target).startsWith('conv_')) return target;
          return String(normalized[0].id);
        });
      } catch (err) {
        console.warn('[App] Could not load server conversations:', err);
      }
    }

    loadServerHistory();
    return () => {
      isMounted = false;
    };
  }, [isAuthenticated, authLoading]);

  const activeConversation = conversations.find((c) => c.id === activeConversationId) || conversations[0] || null;

  const handleNewChat = useCallback(() => {
    const current = conversations.find((c) => c.id === activeConversationId);
    if (current && (!current.messages || current.messages.length === 0)) {
      return current.id;
    }

    const nonEmpty = conversations.filter((c) => c.messages && c.messages.length > 0);
    const newConv = createNewConversation('New Conversation');
    setConversations([newConv, ...nonEmpty]);
    setActiveConversationId(newConv.id);
    return newConv.id;
  }, [conversations, activeConversationId]);

  const handleSelectConversation = useCallback(async (id) => {
    if (!id) return;
    setActiveConversationId(id);

    // Remove any abandoned empty drafts when switching away
    setConversations((prev) => prev.filter((c) => c.id === id || (c.messages && c.messages.length > 0)));

    if (!id.startsWith('conv_') && isAuthenticated && getAuthToken()) {
      try {
        const details = await fetchConversation(id);
        if (details?.id) {
          setConversations((prev) =>
            prev.map((c) => {
              if (String(c.id) !== String(id)) return c;
              return {
                ...c,
                title: details.title || c.title,
                messages: Array.isArray(details.messages) ? details.messages : c.messages || [],
                updatedAt: details.updatedAt || details.updated_at || c.updatedAt,
              };
            })
          );
        }
      } catch (err) {
        console.warn(`[App] Failed to fetch history for conversation ${id}:`, err);
      }
    }
  }, [isAuthenticated]);

  const handleSendMessage = useCallback(async (userText) => {
    const text = userText?.trim();
    if (!text || isLoading) return;

    let targetId = activeConversationId;
    let targetConv = conversations.find((c) => c.id === targetId);

    if (!targetConv) {
      targetConv = createNewConversation('New Conversation');
      targetId = targetConv.id;
      setConversations((prev) => [targetConv, ...prev]);
      setActiveConversationId(targetId);
    }

    const userMessage = {
      id: `msg_${Date.now()}_u`,
      sender: 'user',
      text,
      timestamp: new Date().toISOString(),
    };

    const isFirstMessage = !targetConv.messages || targetConv.messages.length === 0;
    const shortTitle = text.length > 36 ? `${text.slice(0, 36).trim()}...` : text;

    setConversations((prev) =>
      prev.map((c) => {
        if (c.id !== targetId) return c;
        return {
          ...c,
          title: isFirstMessage || c.title === 'New Conversation' ? shortTitle : c.title,
          updatedAt: new Date().toISOString(),
          messages: [...(c.messages || []), userMessage],
        };
      })
    );

    setIsLoading(true);

    try {
      const serverIdToSend = targetId && !targetId.startsWith('conv_') ? targetId : null;
      const result = await sendChatMessage(text, serverIdToSend);

      const assistantMessage = {
        id: `msg_${Date.now()}_a`,
        sender: 'assistant',
        text: result.answer || 'No response received from assistant.',
        matched: result.matched !== undefined ? result.matched : true,
        category: result.category || null,
        sources: result.sources || [],
        timestamp: result.timestamp || new Date().toISOString(),
      };

      const resolvedId = result.conversation_id ? String(result.conversation_id) : targetId;

      setConversations((prev) =>
        prev.map((c) => {
          if (c.id !== targetId) return c;
          return {
            ...c,
            id: resolvedId,
            updatedAt: new Date().toISOString(),
            messages: [...(c.messages || []), assistantMessage],
          };
        })
      );

      setActiveConversationId(resolvedId);
    } catch (err) {
      console.error('[App] Error receiving chat response:', err);

      const errorMessage = {
        id: `msg_${Date.now()}_err`,
        sender: 'assistant',
        text: 'Unable to connect to the assistant server. Please verify the backend is running and try again.',
        matched: false,
        isError: true,
        failedQuestion: text,
        category: null,
        sources: [],
        timestamp: new Date().toISOString(),
      };

      setConversations((prev) =>
        prev.map((c) => {
          if (c.id !== targetId) return c;
          return {
            ...c,
            updatedAt: new Date().toISOString(),
            messages: [...(c.messages || []), errorMessage],
          };
        })
      );
    } finally {
      setIsLoading(false);
    }
  }, [activeConversationId, conversations, isLoading]);

  const handleClearConversation = useCallback(async () => {
    if (!activeConversationId) return;

    if (!activeConversationId.startsWith('conv_') && isAuthenticated && getAuthToken()) {
      try {
        await clearConversation(activeConversationId);
      } catch (err) {
        console.warn(`[App] Failed to clear conversation ${activeConversationId}:`, err);
      }
    }

    setConversations((prev) =>
      prev.map((c) => {
        if (c.id !== activeConversationId) return c;
        return {
          ...c,
          title: 'New Conversation',
          messages: [],
          updatedAt: new Date().toISOString(),
        };
      })
    );
  }, [activeConversationId, isAuthenticated]);

  const handleResetAllData = useCallback(() => {
    const fresh = createNewConversation('New Conversation');
    setConversations([fresh]);
    setActiveConversationId(fresh.id);
  }, []);

  const handleAskInChat = useCallback((question, targetConversationId = null) => {
    const clean = question?.trim();
    if (!clean) return;

    let targetId = targetConversationId || activeConversationId;
    let targetConv = conversations.find((c) => c.id === targetId);

    if (!targetConv) {
      targetConv = createNewConversation('New Conversation');
      targetId = targetConv.id;
      setConversations((prev) => [targetConv, ...prev]);
    }

    setActiveConversationId(targetId);

    navigate('/', {
      state: {
        askQuestion: clean,
        targetConversationId: targetId,
        timestamp: Date.now(),
      },
    });
  }, [activeConversationId, conversations, navigate]);

  return (
    <div className="app-layout-shell">
      <Sidebar
        isOpen={isSidebarOpen}
        onClose={() => setIsSidebarOpen(false)}
        conversations={conversations}
        activeConversationId={activeConversationId}
        onSelectConversation={handleSelectConversation}
        onNewChat={handleNewChat}
        onOpenSettings={() => setIsSettingsOpen(true)}
      />

      <div className="app-workspace">
        <Routes>
          <Route
            path="/"
            element={
              <ChatPage
                activeConversation={activeConversation}
                isLoading={isLoading}
                onSendMessage={handleSendMessage}
                onClearConversation={handleClearConversation}
                onToggleSidebar={() => setIsSidebarOpen((prev) => !prev)}
              />
            }
          />
          <Route path="/faq" element={<FAQPage onAskInChat={handleAskInChat} />} />
          <Route
            path="/sources/:id"
            element={<SourceDetailPage activeConversationId={activeConversationId} onAskInChat={handleAskInChat} />}
          />
          <Route
            path="/source/:id"
            element={<SourceDetailPage activeConversationId={activeConversationId} onAskInChat={handleAskInChat} />}
          />
          <Route path="/about" element={<AboutPage />} />
          <Route
            path="*"
            element={
              <ChatPage
                activeConversation={activeConversation}
                isLoading={isLoading}
                onSendMessage={handleSendMessage}
                onClearConversation={handleClearConversation}
                onToggleSidebar={() => setIsSidebarOpen((prev) => !prev)}
              />
            }
          />
        </Routes>
      </div>

      <SettingsModal
        isOpen={isSettingsOpen}
        onClose={() => setIsSettingsOpen(false)}
        onResetAllData={handleResetAllData}
      />
    </div>
  );
}

export default function App() {
  return (
    <AuthGate>
      <ChatApplication />
    </AuthGate>
  );
}
